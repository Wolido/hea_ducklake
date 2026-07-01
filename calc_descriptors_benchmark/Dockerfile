#FROM python:3.14-bookworm-slim
FROM registry.cn-beijing.aliyuncs.com/wolido/python:3.13-x86

# 安装容器内存监测工具（procps 提供 ps/free/top 等）及 psutil 编译依赖
RUN if command -v apt-get >/dev/null 2>&1; then \
        apt-get update && apt-get install -y --no-install-recommends procps gcc python3-dev && rm -rf /var/lib/apt/lists/*; \
    elif command -v apk >/dev/null 2>&1; then \
        apk add --no-cache procps gcc musl-dev python3-dev; \
    fi

COPY ./calc_py /root/calc_py
WORKDIR /root/calc_py
RUN pip install -r requirements.txt
# 还需要编译一个calc_faster_rs的wheel，也使用pip安装
RUN pip install rs_calc_faster-0.1.1-cp313-cp313-manylinux_2_34_x86_64.whl

ENV PYTHONPATH=/root
# Redis提前配置好
ENV GSHJ_REDIS_HOST_1=xxx

ENV GSHJ_REDIS_PORT_1=xxx
ENV GSHJ_REDIS_PASSWORD=xxx
ENV GSHJ_CSV_DIR=/root/calc_csv/



CMD ["python", "main.py"]
# 任务发送队列需要以下命令
# CMD ["python", "que_push.py"]



