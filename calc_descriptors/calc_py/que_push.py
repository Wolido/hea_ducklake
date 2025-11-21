"""
2024.12.27
Author: IDM-D
更快地向队列发送数据
"""

from itertools import combinations
import time
import redis
import rs_calc_faster # type: ignore
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

r1 = redis.StrictRedis(host=redis_host_1, port=redis_port_int_1, password=redis_password)
r2 = redis.StrictRedis(host=redis_host_2, port=redis_port_int_2, password=redis_password)
r3 = redis.StrictRedis(host=redis_host_3, port=redis_port_int_3, password=redis_password)
r4 = redis.StrictRedis(host=redis_host_4, port=redis_port_int_4, password=redis_password)

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


# con_index计算
# pylint: disable=no-member
con_list: list[list[int]] = rs_calc_faster.rs_generate_con_list_all()


# main_process
PROCESS_NUM: int = 1
for elem_index, elem_iter in enumerate(elem_tuple):
    # pylint: disable=no-member
    redis_list: list[str] = rs_calc_faster.rs_que_push_iter(
        elem_index=elem_index, elem_tuple=elem_iter, con_list=con_list
    )
    match PROCESS_NUM:
        case 1:
            while True:
                if r1.llen("condata") == 0:
                    break
                time.sleep(5)
            r1.rpush("condata", *redis_list)
            PROCESS_NUM += 1
        case 2:
            while True:
                if r2.llen("condata") == 0:
                    break
                time.sleep(5)
            r2.rpush("condata", *redis_list)
            PROCESS_NUM += 1
        case 3:
            while True:
                if r3.llen("condata") == 0:
                    break
                time.sleep(5)
            r3.rpush("condata", *redis_list)
            PROCESS_NUM += 1
        case 4:
            while True:
                if r4.llen("condata") == 0:
                    break
                time.sleep(5)
            r4.rpush("condata", *redis_list)
            PROCESS_NUM = 1