"""
Author: IDM-D
计算核心调度程序
"""

import gc
import logging
import os
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any

import redis
import rs_calc_faster  # type: ignore

import numpy as np
from numpy import ndarray

from models import CALCDATA, CONDATA
from pipe import get_info_from_que_large, push_calc_data_list, r1


# 配置日志
LOG_FILE: Path = Path(__file__).parent / "main.log"
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

from calc_faster import (  # noqa: E402
    calc_G_G0,
    calc_Hmix,
    calc_K_G,
    calc_Smix,
    calc_Tb_Tm,
    calc_ave,
    calc_gamma,
    calc_have_zero,
    calc_lambda,
    calc_params_WEF,
    calc_reciprocal_omega,
    calc_rmse,
    calc_range,
    calc_pair,
    calc_rmse_Hmix,
    con_to_array,
    generate_hmix_con,
    generate_params_4_array,
    generate_params_array,
    make_ave_params,
)


# 设置退出机制
exit_flag: bool = False

# 模块级变量，用于内存增量统计与峰值追踪
_last_usage_mb: float | None = None
_peak_usage_mb: float = 0.0
_peak_sampling_stop: threading.Event = threading.Event()


def reset_memory_baseline() -> None:
    """重置内存基线，用于新一轮增量统计。"""
    global _last_usage_mb
    _last_usage_mb = None


def get_memory_mb() -> float | None:
    """读取当前容器/进程内存使用量（MB），失败返回 None。"""
    usage_bytes: int | None = None

    # cgroup v2
    if os.path.exists("/sys/fs/cgroup/memory.current"):
        try:
            with open("/sys/fs/cgroup/memory.current", "r") as f:
                usage_bytes = int(f.read().strip())
        except (OSError, ValueError):
            pass
    # cgroup v1
    elif os.path.exists("/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            with open("/sys/fs/cgroup/memory/memory.usage_in_bytes", "r") as f:
                usage_bytes = int(f.read().strip())
        except (OSError, ValueError):
            pass

    if usage_bytes is not None:
        return usage_bytes / 1024 / 1024

    # 回退到 psutil
    try:
        import psutil
        proc = psutil.Process()
        return proc.memory_info().rss / 1024 / 1024
    except Exception:
        return None


def _peak_sampling_worker(interval: float = 0.2) -> None:
    """后台线程：持续采样内存并更新全局峰值。"""
    global _peak_usage_mb
    while not _peak_sampling_stop.is_set():
        current = get_memory_mb()
        if current is not None and current > _peak_usage_mb:
            _peak_usage_mb = current
        time.sleep(interval)


def start_peak_tracking(interval: float = 0.2) -> None:
    """启动后台峰值采样线程。"""
    global _peak_usage_mb
    _peak_usage_mb = 0.0
    _peak_sampling_stop.clear()
    t = threading.Thread(target=_peak_sampling_worker, args=(interval,), daemon=True)
    t.start()


def stop_peak_tracking() -> float:
    """停止后台峰值采样并返回期间记录到的最大内存（MB）。"""
    _peak_sampling_stop.set()
    # 给工作线程最后一次采样机会
    time.sleep(0.05)
    return _peak_usage_mb


def sigterm_handler(signum: int, frame: Any) -> None:
    global exit_flag
    exit_flag = True


signal.signal(signal.SIGTERM, sigterm_handler)


def calc_main_progress(condata: CONDATA) -> CALCDATA:
    """
    主任务流程序-计算部分
    """
    con_tuple: tuple[float, ...] = (
        condata.con1,
        condata.con2,
        condata.con3,
        condata.con4,
        condata.con5,
        condata.con6,
    )

    elements_tuple: tuple[str, ...] = (
        condata.elem1,
        condata.elem2,
        condata.elem3,
        condata.elem4,
        condata.elem5,
        condata.elem6,
    )

    con_array: ndarray = con_to_array(con_tuple=con_tuple)
    hmix_con: ndarray = generate_hmix_con(elements_tuple=elements_tuple)
    params_array: ndarray = generate_params_array(elements_tuple=elements_tuple).T

    params_4_array: ndarray = generate_params_4_array(elements_tuple=elements_tuple).T

    ave_array: ndarray = calc_ave(con_array=con_array, params_array=params_array)
    ave_params: ndarray = make_ave_params(ave_array=ave_array)
    rmse_array: ndarray = calc_rmse(
        con_array=con_array, ave_params=ave_params, params_array=params_array
    )
    range_array: ndarray = calc_range(
        con_array=con_array, ave_params=ave_params, params_array=params_array
    )
    pair_array: ndarray = calc_pair(con_array=con_array, params_array=params_array)

    Smix_data: float = calc_Smix(con_array=con_array)
    lambda_data: float = calc_lambda(Smix_data=Smix_data, rmse_r=rmse_array[29])
    gamma_data: float = calc_gamma(params_array=params_array, ave_r=ave_array[29])
    # Ev_data: float = calc_Ev(con_array=con_array, params_array=params_array)
    # pylint: disable=no-member
    Ev_data: float = rs_calc_faster.rs_calc_ev(
        con_list=list(con_array), params_list=list(params_array)
    )
    GG0_data: float = calc_G_G0(G=ave_array[16], G0=ave_array[27])
    KG_data: float = calc_K_G(K=ave_array[15], G=ave_array[16])
    TbTm_data: float = calc_Tb_Tm(Tb=ave_array[35], Tm=ave_array[34])

    Hmix_data: float = calc_Hmix(con_array=con_array, Hmix_con=hmix_con)
    rmse_Hmix_data: float = calc_rmse_Hmix(
        con_array=con_array, Hmix_data=Hmix_data, Hmix_con=hmix_con
    )
    omega_data: float = calc_reciprocal_omega(
        Smix_data=Smix_data, Hmix_data=Hmix_data, Tm=ave_array[34]
    )

    ave_WEF: float
    rmse_WEF: float
    range_WEF: float
    pair_WEF: float
    ave_WEF, rmse_WEF, range_WEF, pair_WEF = calc_params_WEF(
        con_array=con_array, WEF_con=params_4_array[0]
    )
    ave_array = np.append(ave_array, ave_WEF)
    rmse_array = np.append(rmse_array, rmse_WEF)
    range_array = np.append(range_array, range_WEF)
    pair_array = np.append(pair_array, pair_WEF)

    for index in (1, 2, 3):
        params_array_with_zero: ndarray = params_4_array[index]
        ave_with_zero: float
        rmse_with_zero: float
        range_with_zero: float
        pair_with_zero: float
        ave_with_zero, rmse_with_zero, range_with_zero, pair_with_zero = calc_have_zero(
            con_array=con_array, params_array_with_zero=params_array_with_zero
        )
        ave_array = np.append(ave_array, ave_with_zero)
        rmse_array = np.append(rmse_array, rmse_with_zero)
        range_array = np.append(range_array, range_with_zero)
        pair_array = np.append(pair_array, pair_with_zero)

    # pylint: disable=no-member
    ave_array_list: list = rs_calc_faster.rs_round_array(list(ave_array))
    rmse_array_list: list =rs_calc_faster.rs_round_array(list(rmse_array))
    range_array_list: list =rs_calc_faster.rs_round_array(list(range_array))
    pair_array_list: list = rs_calc_faster.rs_round_array(list(pair_array))
    Smix_data = round(Smix_data, 5)
    lambda_data = round(lambda_data, 5)
    gamma_data = round(gamma_data, 5)
    Ev_data = round(Ev_data, 5)
    GG0_data = round(GG0_data, 5)
    KG_data = round(KG_data, 5)
    TbTm_data = round(TbTm_data, 5)
    Hmix_data = round(Hmix_data, 5)
    rmse_Hmix_data = round(rmse_Hmix_data, 5)
    omega_data = round(omega_data, 5)

    calc_data: CALCDATA = CALCDATA(
        con_index=condata.con_index,
        elem_index=condata.elem_index,
        ave_array_list=ave_array_list,
        rmse_array_list=rmse_array_list,
        range_array_list=range_array_list,
        pair_array_list=pair_array_list,
        Smix_data=Smix_data,
        lambda_data=lambda_data,
        gamma_data=gamma_data,
        Ev_data=Ev_data,
        GG0_data=GG0_data,
        KG_data=KG_data,
        TbTm_data=TbTm_data,
        Hmix_data=Hmix_data,
        rmse_Hmix_data=rmse_Hmix_data,
        omega_data=omega_data,
    )

    return calc_data


def log_memory_usage(label: str = "") -> None:
    """打印当前容器内存使用情况（优先读取 cgroup，否则回退到 psutil），支持阶段标签和增量计算。"""
    global _last_usage_mb
    usage_bytes: int | None = None
    limit_bytes: int | None = None

    # cgroup v2
    if os.path.exists("/sys/fs/cgroup/memory.current"):
        try:
            with open("/sys/fs/cgroup/memory.current", "r") as f:
                usage_bytes = int(f.read().strip())
            if os.path.exists("/sys/fs/cgroup/memory.max"):
                with open("/sys/fs/cgroup/memory.max", "r") as f:
                    limit_val = f.read().strip()
                    if limit_val != "max":
                        limit_bytes = int(limit_val)
        except (OSError, ValueError):
            pass
    # cgroup v1
    elif os.path.exists("/sys/fs/cgroup/memory/memory.usage_in_bytes"):
        try:
            with open("/sys/fs/cgroup/memory/memory.usage_in_bytes", "r") as f:
                usage_bytes = int(f.read().strip())
            if os.path.exists("/sys/fs/cgroup/memory/memory.limit_in_bytes"):
                with open("/sys/fs/cgroup/memory/memory.limit_in_bytes", "r") as f:
                    raw_limit = f.read().strip()
                    limit_bytes = int(raw_limit)
                    # v1 未限制时返回接近 int64 max 的极大值
                    if limit_bytes > (1 << 60):
                        limit_bytes = None
        except (OSError, ValueError):
            pass

    if usage_bytes is not None:
        usage_mb = usage_bytes / 1024 / 1024
        msg = "容器内存使用"
        if label:
            msg += f" [{label}]"
        msg += f": {usage_mb:.2f} MB"
        if _last_usage_mb is not None:
            delta = usage_mb - _last_usage_mb
            msg += f" (Δ {delta:+.2f} MB)"
        _last_usage_mb = usage_mb
        if limit_bytes:
            limit_mb = limit_bytes / 1024 / 1024
            percent = (usage_bytes / limit_bytes) * 100
            msg += f" / {limit_mb:.2f} MB ({percent:.2f}%)"
        logger.info(msg)
        return

    # 回退到 psutil（读取进程级 RSS）
    try:
        import psutil
        proc = psutil.Process()
        rss_mb = proc.memory_info().rss / 1024 / 1024
        msg = "进程内存使用 (RSS)"
        if label:
            msg += f" [{label}]"
        msg += f": {rss_mb:.2f} MB"
        if _last_usage_mb is not None:
            delta = rss_mb - _last_usage_mb
            msg += f" (Δ {delta:+.2f} MB)"
        _last_usage_mb = rss_mb
        logger.info(msg)
    except Exception:
        logger.warning("无法获取内存使用信息")


def main_progress() -> None:
    logger.info("开始从Redis批量拉取任务")

    # 重置内存基线，开始新一轮增量统计
    reset_memory_baseline()

    # 从消息队列批量获取任务参数（默认20万条）
    task_list, err = get_info_from_que_large()
    if err is not None:
        logger.error(f"拉取任务失败: {err}")
        return

    logger.info(f"成功拉取 {len(task_list)} 条任务")
    log_memory_usage("拉取任务后")

    # 启动后台峰值采样线程（覆盖计算 + 推送全周期）
    start_peak_tracking(interval=0.2)

    # 批量计算，结果存入 results_batch
    results_batch: list[CALCDATA] = []
    for task_dict in task_list:
        condata = CONDATA(**task_dict)
        calc_data: CALCDATA = calc_main_progress(condata=condata)
        results_batch.append(calc_data)

    log_memory_usage("计算完成后")

    # 统一推送计算结果到 Redis（pipeline 会缓冲序列化后的 JSON，此处记录推送峰值）
    log_memory_usage("推送Redis前")
    push_calc_data_list(results_batch)
    log_memory_usage("推送Redis后")

    # 停止峰值采样并获取周期内最大内存
    peak_mb = stop_peak_tracking()
    logger.info(f"本批次内存峰值: {peak_mb:.2f} MB")

    logger.info(f"计算完成，共 {len(results_batch)} 条结果已批量推送到Redis")

    # 显式释放大对象并强制回收，避免跨轮次内存基线虚高
    del results_batch
    del task_list
    gc.collect()
    log_memory_usage("回收后基线")


if __name__ == "__main__":
    while True:
        main_progress()

        # 退出机制检查，生效后会在接收到 SIGTERM 信号后退出循环
        if exit_flag is True:
            break