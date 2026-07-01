# 2024.12.23
# Author: IDM-D
# 从消息队列读和写数据

import json
import logging
import sys
from pathlib import Path
from typing import Any

import redis
from config import redis_host_1, redis_password, redis_port_int_1
from models import CALCDATA


# 日志配置
LOG_FILE: Path = Path(__file__).parent / "pipe.log"
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    _formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _fh = logging.FileHandler(LOG_FILE)
    _fh.setFormatter(_formatter)
    logger.addHandler(_fh)
    _sh = logging.StreamHandler(sys.stdout)
    _sh.setFormatter(_formatter)
    logger.addHandler(_sh)
    logger.propagate = False

# 使用连接池建立长连接，避免频繁创建/销毁连接带来的开销
_pool = redis.ConnectionPool(
    host=redis_host_1,
    port=redis_port_int_1,
    password=redis_password,
    decode_responses=False,
    socket_keepalive=True,
    socket_keepalive_options={},
    health_check_interval=30,
    socket_connect_timeout=10,
    socket_timeout=30,
    max_connections=10,
)
r = redis.StrictRedis(connection_pool=_pool)

r1 = r


def get_info_from_que_large(
    target_count: int = 200_000, batch_size: int = 200_000
) -> tuple[list[dict], Exception | None]:
    """
    从消息队列中批量获取大量数据（默认20万条），存放到列表中返回。

    设计说明：
    - blpop 不支持 count，只能单条弹出；若用它取20万条会产生20万次网络RTT，不可行。
    - 因此采用 "blpop 阻塞等第一条 + lpop count 批量取剩余" 的混合策略。
    - batch_size 默认 20万，直接一次性拉取，最大限度减少网络 RTT。

    target_count: 目标获取条数
    batch_size:   每批拉取条数
    return: (任务列表, None) 或 ([], Exception)
    """
    try:
        tasks: list[dict] = []

        # 1. blpop 阻塞等待第一个任务，避免空转
        message = r.blpop(["condata"], timeout=1)
        if isinstance(message, tuple):
            _, message_json = message
            tasks.append(json.loads(message_json))
        else:
            return (tasks, ValueError("No data"))

        # 2. lpop count 批量快速取完剩余任务
        while len(tasks) < target_count:
            remaining = target_count - len(tasks)
            current_batch = min(batch_size, remaining)

            batch: list[Any] | None = r.lpop("condata", count=current_batch)
            if not batch:
                break

            for item in batch:
                tasks.append(json.loads(item))

            # 每拉够 10 万条记录一次进度（便于监控百万级数据拉取）
            if len(tasks) % 100_000 < current_batch:
                logger.info(f"已从Redis拉取 {len(tasks)} 条任务")

        return (tasks, None)
    except Exception as e:
        return ([], e)

def get_info_from_que() -> tuple[dict, Exception | None]:
    """
    从消息队列中获取数据（一条）

    return: 任务参数
    rtype: dict
    """
    try:
        # 从redis里面拉取一条数据
        message = r.blpop(["condata"], timeout=1)
        if isinstance(message, tuple):
            _, message_json = message
            message_dict = json.loads(message_json)
        else:
            return ({}, ValueError("No data"))
        return (message_dict, None)
    except Exception as e:
        return ({}, e)


def push_calc_data_to_que(calc_data: CALCDATA, que_name: str) -> None:
    """
    将准备填写数据库的数据写入消息队列

    calc_data: 计算得到的数据
    calc_data type: CALCDATA，构建的数据类

    return: None
    """
    data_dict = {
        "con_index": calc_data.con_index,
        "elem_index": calc_data.elem_index,
        "ave_array": calc_data.ave_array_list,
        "rmse_array": calc_data.rmse_array_list,
        "range_array": calc_data.range_array_list,
        "pair_array": calc_data.pair_array_list,
        "Smix_data": calc_data.Smix_data,
        "lambda_data": calc_data.lambda_data,
        "gamma_data": calc_data.gamma_data,
        "Ev_data": calc_data.Ev_data,
        "GG0_data": calc_data.GG0_data,
        "KG_data": calc_data.KG_data,
        "TbTm_data": calc_data.TbTm_data,
        "Hmix_data": calc_data.Hmix_data,
        "rmse_Hmix_data": calc_data.rmse_Hmix_data,
        "omega_data": calc_data.omega_data,
    }

    json_to_push = json.dumps(data_dict)
    r.rpush(que_name, json_to_push)


def push_calc_data_list(calc_data_list: list[CALCDATA]) -> None:
    """
    将批量计算结果按 elem_index 分组写入对应 Redis 队列。

    calc_data_list: 计算结果列表
    """
    if not calc_data_list:
        return

    with r.pipeline() as pipe:
        for calc_data in calc_data_list:
            data_dict = {
                "con_index": calc_data.con_index,
                "elem_index": calc_data.elem_index,
                "ave_array": calc_data.ave_array_list,
                "rmse_array": calc_data.rmse_array_list,
                "range_array": calc_data.range_array_list,
                "pair_array": calc_data.pair_array_list,
                "Smix_data": calc_data.Smix_data,
                "lambda_data": calc_data.lambda_data,
                "gamma_data": calc_data.gamma_data,
                "Ev_data": calc_data.Ev_data,
                "GG0_data": calc_data.GG0_data,
                "KG_data": calc_data.KG_data,
                "TbTm_data": calc_data.TbTm_data,
                "Hmix_data": calc_data.Hmix_data,
                "rmse_Hmix_data": calc_data.rmse_Hmix_data,
                "omega_data": calc_data.omega_data,
            }
            que_name = f"calc_data_{calc_data.elem_index}"
            pipe.rpush(que_name, json.dumps(data_dict))
        pipe.execute()

