"""
Author: IDM-D
基础设置参数，以及从环境变量的读取参数
"""
import os


# redis
redis_host_1: str = os.getenv("GSHJ_REDIS_HOST_1", "redis_1")
redis_host_2: str = os.getenv("GSHJ_REDIS_HOST_2", "redis_2")
redis_host_3: str = os.getenv("GSHJ_REDIS_HOST_3", "redis_3")
redis_host_4: str = os.getenv("GSHJ_REDIS_HOST_4", "redis_4")
redis_port_1: str = os.getenv("GSHJ_REDIS_PORT_1", "6379")
redis_port_2: str = os.getenv("GSHJ_REDIS_PORT_2", "6379")
redis_port_3: str = os.getenv("GSHJ_REDIS_PORT_3", "6379")
redis_port_4: str = os.getenv("GSHJ_REDIS_PORT_4", "6379")
redis_password: str = os.getenv("GSHJ_REDIS_PASSWORD", "XXXXXXXX")

redis_port_int_1: int = int(redis_port_1)
redis_port_int_2: int = int(redis_port_2)
redis_port_int_3: int = int(redis_port_3)
redis_port_int_4: int = int(redis_port_4)