"""
Author: IDM-D
基础设置参数，以及从环境变量的读取参数
"""
import os


# redis
redis_host_1: str = os.getenv("GSHJ_REDIS_HOST_1", "xxx")

redis_port_1: str = os.getenv("GSHJ_REDIS_PORT_1", "xxx")

redis_password: str = os.getenv("GSHJ_REDIS_PASSWORD", "xxx")

redis_port_int_1: int = int(redis_port_1)



csv_dir: str = os.getenv("GSHJ_CSV_DIR", "")