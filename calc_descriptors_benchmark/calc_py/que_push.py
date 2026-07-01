"""
2024.12.27
Author: IDM-D
更快地向队列发送数据
"""

from itertools import combinations
import time
import logging
import sys
from pathlib import Path
import redis
import rs_calc_faster  # type: ignore
from config import (
    redis_host_1,
    redis_password,
    redis_port_int_1
)

r1 = redis.StrictRedis(host=redis_host_1, port=redis_port_int_1, password=redis_password)

LOG_FILE = Path(__file__).parent / "que_push.log"
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

# elem_index计算
elements = [
    "Fe",
    "Ni",
    "Mn",
    "Al",
    "Cr",
    "Cu",
    "Co",
    "Mo",
    "Ti",
    "Nb",
    "Ta",
    "W",
    "V",
    "Zr",
    "Hf",
]
# 使用itertools.combinations生成所有6个元素的组合
elem_tuple: tuple[tuple[str, ...], ...] = tuple(combinations(elements, 6))


def chunked_push(redis_list: list[str], batch_size: int = 50_000) -> None:
    """分块批量推送到 Redis，避免单命令过大导致阻塞或超时。"""
    total = len(redis_list)
    pushed = 0
    start = time.time()

    for i in range(0, total, batch_size):
        batch = redis_list[i:i + batch_size]
        with r1.pipeline() as pipe:
            for item in batch:
                pipe.rpush("condata", item)
            pipe.execute()

        pushed += len(batch)
        elapsed = time.time() - start
        logger.info(
            f"已推送 {pushed:,} / {total:,} 条 ({pushed / total * 100:.1f}%), "
            f"耗时 {elapsed:.1f}s"
        )


if __name__ == "__main__":
    # con_index计算
    # pylint: disable=no-member
    con_list: list[list[int]] = rs_calc_faster.rs_generate_con_list_all()
    logger.info(f"浓度组合总数: {len(con_list):,}")

    # 仅处理第一个组合，并推送到 Redis
    elem_index, elem_iter = 0, elem_tuple[0]
    logger.info(f"开始生成任务数据: elem_index={elem_index}, elements={elem_iter}")

    t0 = time.time()
    redis_list: list[str] = rs_calc_faster.rs_que_push_iter(
        elem_index=elem_index,
        elem_tuple=elem_iter,
        con_list=con_list
    )
    logger.info(f"任务数据生成完成，共 {len(redis_list):,} 条，耗时 {time.time() - t0:.1f}s")

    chunked_push(redis_list, batch_size=50_000)
    logger.info("全部推送完成")
