FROM python:3.14-bookworm-slim

COPY ./calc_py /root/calc_py
WORKDIR /root/calc_py
RUN pip install -r requirements.txt
# 还需要编译一个calc_faster_rs的wheel，也使用pip安装

ENV PYTHONPATH=/root
# Redis提前配置好
ENV GSHJ_REDIS_HOST_1=XXXX
ENV GSHJ_REDIS_HOST_2=XXXX
ENV GSHJ_REDIS_HOST_3=XXXX
ENV GSHJ_REDIS_HOST_4=XXXX
ENV GSHJ_REDIS_PORT_1=XXXX
ENV GSHJ_REDIS_PORT_2=XXXX
ENV GSHJ_REDIS_PORT_3=XXXX
ENV GSHJ_REDIS_PORT_4=XXXX

CMD ["python", "main.py"]
# 任务发送队列需要以下命令
# CMD ["python", "que_push.py"]



