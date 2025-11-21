# 2024.12.23
# Author: IDM-D
# 从消息队列读和写数据

import json
import redis
from config import (
    redis_host_1,
    redis_host_2,
    redis_host_3,
    redis_host_4,
    redis_password,
    redis_port_int_1,
    redis_port_int_2,
    redis_port_int_3,
    redis_port_int_4,
)
from models import CALCDATA


r1 = redis.StrictRedis(host=redis_host_1, port=redis_port_int_1, password=redis_password)
r2 = redis.StrictRedis(host=redis_host_2, port=redis_port_int_2, password=redis_password)
r3 = redis.StrictRedis(host=redis_host_3, port=redis_port_int_3, password=redis_password)
r4 = redis.StrictRedis(host=redis_host_4, port=redis_port_int_4, password=redis_password)


def get_info_from_que(r: redis.StrictRedis) -> tuple[dict, Exception | None]:
    """
    从消息队列中获取数据

    return: 任务参数
    rtype: dict
    """
    try:
        message = r.blpop(["condata"], timeout=1)
        if isinstance(message, tuple):
            _, message_json = message
            message_dict = json.loads(message_json)
        else:
            return ({}, ValueError("No data"))
        return (message_dict, None)
    except Exception as e:
        return ({}, e)


def push_calc_data_to_que(calc_data: CALCDATA, que_name: str, r: redis.StrictRedis) -> None:
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