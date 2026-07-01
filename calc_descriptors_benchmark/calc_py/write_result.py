"""
将计算结果写入csv
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
import signal
from typing import Any
import redis
from config import (
    redis_host_1,
    redis_port_int_1,
    redis_password,
    csv_dir,
)

# 日志配置
LOG_FILE: Path = Path(__file__).parent / "write_result.log"
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

r1 = redis.StrictRedis(
    host=redis_host_1, port=redis_port_int_1, password=redis_password
)


# 设置退出机制
exit_flag: bool = False


def sigterm_handler(signum: int, frame: Any) -> None:
    global exit_flag
    exit_flag = True


signal.signal(signal.SIGTERM, sigterm_handler)


def get_calc_data_from_que(elem_index: int) -> tuple[dict, Exception | None]:
    """
    从消息队列中获取数据

    return: (解析后的数据字典, None) 或 ({}, Exception)
    """
    try:
        message = r1.blpop([f"calc_data_{elem_index}"], timeout=1)
        if isinstance(message, tuple):
            _, message_byte = message
            data_dict = json.loads(message_byte.decode())
            return (data_dict, None)
        else:
            return ({}, ValueError("No data"))
    except Exception as e:
        return ({}, e)


def read_and_write() -> None:
    """
    从单个Redis读取队列数据并写入CSV文件。
    每次调用处理一个有数据的队列，处理完后返回。

    通用方案，先用csv方法，把数据从队列放入硬盘
    duckdb的cli再处理csv文件速度很快
    """
    for i in range(1, 5006):
        if exit_flag:
            break

        if not r1.exists(f"calc_data_{i}"):
            continue

        csv_path = (
            f"{csv_dir}calc_data_{i}_{datetime.now().strftime('%Y%m%d%H%M%S%f')}.csv"
        )
        logger.info(f"开始从队列 calc_data_{i} 读取数据并写入 {csv_path}")

        with open(csv_path, encoding="utf-8", mode="a") as file:
            data_buffer: list[str] = []
            processed_count: int = 0
            while True:
                data_dict, err = get_calc_data_from_que(elem_index=i)
                if err is not None:
                    if data_buffer:
                        file.write("\n".join(data_buffer) + "\n")
                    break

                all_numbers: list[str] = []
                all_numbers.extend(data_dict["ave_array"])
                all_numbers.extend(data_dict["rmse_array"])
                all_numbers.extend(data_dict["range_array"])
                all_numbers.extend(data_dict["pair_array"])

                scalar_keys = [
                    "Smix_data",
                    "lambda_data",
                    "gamma_data",
                    "Ev_data",
                    "GG0_data",
                    "KG_data",
                    "TbTm_data",
                    "Hmix_data",
                    "rmse_Hmix_data",
                    "omega_data",
                ]

                for key in scalar_keys:
                    all_numbers.append(data_dict[key])

                csv_line: str = ",".join(str(x) for x in all_numbers)
                data_buffer.append(csv_line)
                processed_count += 1

                if len(data_buffer) >= 1000:
                    file.write("\n".join(data_buffer) + "\n")
                    data_buffer = []

            logger.info(f"队列 calc_data_{i} 数据写入完成，共处理 {processed_count} 条")
            break


if __name__ == "__main__":
    while True:
        read_and_write()
        if exit_flag is True:
            break