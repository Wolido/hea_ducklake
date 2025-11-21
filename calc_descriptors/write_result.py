"""
将计算结果写入csv
"""

from datetime import datetime
import signal
from typing import Any
import redis
from config import (
    redis_host_1,
    redis_host_2,
    redis_host_3,
    redis_host_4,
    redis_port_int_1,
    redis_port_int_2,
    redis_port_int_3,
    redis_port_int_4,
    redis_password,
    csv_dir
)


r1 = redis.StrictRedis(
    host=redis_host_1, port=redis_port_int_1, password=redis_password
)
r2 = redis.StrictRedis(
    host=redis_host_2, port=redis_port_int_2, password=redis_password
)
r3 = redis.StrictRedis(
    host=redis_host_3, port=redis_port_int_3, password=redis_password
)
r4 = redis.StrictRedis(
    host=redis_host_4, port=redis_port_int_4, password=redis_password
)


# 设置退出机制
exit_flag: bool = False


def sigterm_handler(signum: int, frame: Any) -> None:
    global exit_flag
    exit_flag = True


signal.signal(signal.SIGTERM, sigterm_handler)


def get_calc_data_from_que(r: redis.StrictRedis, elem_index: int) -> tuple[str, Exception | None]:
    """
    从消息队列中获取数据

    return: 任务参数
    rtype: str
    """
    try:
        message = r.blpop([f"calc_data_{elem_index}"], timeout=1)
        if isinstance(message, tuple):
            _, message_byte = message
            message_json = message_byte.decode()
        else:
            return ("", ValueError("No data"))
        return (message_json, None)
    except Exception as e:
        return ("", e)


def read_and_write(r: redis.StrictRedis) -> None:
    """
    跨队列的读写循环
    从每个redis连接直到读写完一个队列才跳至下一个
    每个redis连接都从1开始搜索到5005

    通用方案，先用csv方法，多核心并行把数据从队列放入硬盘
    duckdb的cli再处理csv文件速度很快
    """

    for i in range(1, 5006):
        if r.exists(f"calc_data_{i}"):
            with open(
                f"{csv_dir}calc_data_{i}_{datetime.now().strftime("%Y%m%d%H%M%S%f")}.csv",
                encoding="utf-8",
                mode="a",
            ) as file:
                data_buffer: list[str] = []
                count: int = 0
                while True:
                    data_str: str
                    err: Exception | None
                    data_str, err = get_calc_data_from_que(r=r, elem_index=i)
                    if err is None:
                        all_numbers: list[str] = []
                        all_numbers.extend(data_str["ave_array"])
                        all_numbers.extend(data_str["rmse_array"])
                        all_numbers.extend(data_str["range_array"])
                        all_numbers.extend(data_str["pair_array"])

                        scalar_keys = ["Smix_data", "lambda_data", "gamma_data", "Ev_data",
                                       "GG0_data", "KG_data", "TbTm_data", "Hmix_data",
                                       "rmse_Hmix_data", "omega_data"]

                        for key in scalar_keys:
                            all_numbers.append(data_str[key])

                        csv_line: str = ",".join(str(x) for x in all_numbers)
                        data_buffer.append(csv_line)


                        count += 1
                        if count > 1000:
                            file.write("\n".join(data_buffer) + "\n")
                            data_buffer = []
                    else:
                        if data_buffer:
                            file.write("\n".join(data_buffer) + "\n")
                            data_buffer = []
                        break
                break


if __name__ == "__main__":
    PROCESS_NUM: int = 1
    while True:
        match PROCESS_NUM:
            case 1:
                read_and_write(r=r1)
                PROCESS_NUM += 1
            case 2:
                read_and_write(r=r2)
                PROCESS_NUM += 1
            case 3:
                read_and_write(r=r3)
                PROCESS_NUM += 1
            case 4:
                read_and_write(r=r4)
                PROCESS_NUM = 1
        if exit_flag is True:
            break