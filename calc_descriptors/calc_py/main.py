"""
Author: IDM-D
计算核心调度程序
"""

import signal
from typing import Any
import redis
import rs_calc_faster  # type: ignore

import numpy as np
from numpy import ndarray

from models import CALCDATA, CONDATA
from pipe import get_info_from_que, push_calc_data_to_que, r1, r2, r3, r4
from calc_faster import (
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


def main_progress(r: redis.StrictRedis) -> None:
    condata_dict, err = get_info_from_que(r=r)
    if err is not None:
        return
    condata = CONDATA(**condata_dict)
    calc_data: CALCDATA = calc_main_progress(condata=condata)
    elem_index: int = calc_data.elem_index
    que_name: str = f"calc_data_{elem_index}"
    push_calc_data_to_que(calc_data=calc_data, que_name=que_name, r=r)


if __name__ == "__main__":
    PROCESS_NUM = 1
    while True:
        match PROCESS_NUM:
            case 1:
                main_progress(r=r1)
                PROCESS_NUM += 1
            case 2:
                main_progress(r=r2)
                PROCESS_NUM += 1
            case 3:
                main_progress(r=r3)
                PROCESS_NUM += 1
            case 4:
                main_progress(r=r4)
                PROCESS_NUM = 1
        if exit_flag is True:
            break