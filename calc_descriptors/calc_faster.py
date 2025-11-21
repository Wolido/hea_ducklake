"""
Author: IDM-D
计算核心程序
"""

import json

import numpy as np
from numpy import ndarray
import rs_calc_faster  # type: ignore

with open("./params.json", encoding="utf-8") as params:
    params_dict: dict = json.load(params)

with open("./params_4.json", encoding="utf-8") as params_4:
    params_4_dict: dict = json.load(params_4)


# MIX_H: ndarray = np.array(
#     [
#         [0, -2, 0, -11, -1, 13, -1, -5, -17, -16, -15, 0, -7, -25, -21],
#         [-2, 0, -8, -22, -7, 4, 0, -7, -35, -30, -29, -3, -18, -49, -42],
#         [0, -8, 0, -19, 2, 4, -5, 5, -8, -4, -4, 6, -1, -15, -12],
#         [-11, -22, -19, 0, -10, -1, -19, -5, -30, -18, -19, -2, -16, -44, -39],
#         [-1, -7, 2, -10, 0, 12, -4, 0, -7, -7, -7, 1, -2, -12, -9],
#         [13, 4, 4, -1, 12, 0, 6, 19, -9, 3, 2, 22, 5, -23, -17],
#         [-1, 0, -5, -19, -4, 6, 0, -5, -28, -25, -24, -1, -14, -41, -35],
#         [-5, -7, 5, -5, 0, 19, -5, 0, -4, -6, -5, 0, 0, -6, -4],
#         [-17, -35, -8, -30, -7, -9, -28, -4, 0, 2, 1, -6, -2, 0, 0],
#         [-16, -30, -4, -18, -7, 3, -25, -6, 2, 0, 0, -8, -1, 4, 4],
#         [-15, -29, -4, -19, -7, 2, -24, -5, 1, 0, 0, -7, -1, 3, 3],
#         [0, -3, 6, -2, 1, 22, -1, 0, -6, -8, -7, 0, -1, -9, -6],
#         [-7, -18, -1, -16, -2, 5, -14, 0, -2, -1, -1, -1, 0, -4, -2],
#         [-25, -49, -15, -44, -12, -23, -41, -6, 0, 4, 3, -9, -4, 0, 0],
#         [-21, -42, -12, -39, -9, -17, -35, -4, 0, 4, 3, -6, -2, 0, 0],
#     ]
# )


# def generate_hmix_con(elements_tuple: tuple[str, ...]) -> ndarray:
#     """
#     构建用于混合焓计算的矩阵

#     numbers: 计算的六种元素名
#     numbers type: tuple[int]

#     rtype: ndarray
#     """

#     numbers: list[int] = []
#     for element in elements_tuple:
#         numbers.append(params_dict[element]["index"])

#     hmix_con: list[list[int]] = []
#     number1: int
#     number2: int
#     for number1 in numbers:
#         hmix_con_temp: list[int] = []
#         for number2 in numbers:
#             hmix_con_temp.append(MIX_H[number1][number2])
#         hmix_con.append(hmix_con_temp)
#     return np.array(hmix_con)


def generate_hmix_con(elements_tuple: tuple[str, ...]) -> ndarray:
    """
    构建用于混合焓计算的矩阵

    numbers: 计算的六种元素名
    numbers type: tuple[int]

    rtype: ndarray
    """

    # pylint: disable=no-member
    hmix_con: list[list[int]] = rs_calc_faster.rs_generate_hmix_con(
        elem_tuple=elements_tuple
    )
    return np.array(hmix_con)


def generate_params_array(elements_tuple: tuple[str, ...]) -> ndarray:
    """
    构建计算用的描述符矩阵

    elements_tuple: 六种需要计算的元素名
    elements_tuple type: tuple[str, ...]

    rtype: ndarray
    """
    params_list: list[list[float]] = []
    for element in elements_tuple:
        params_list.append(params_dict[element]["params"])
    return np.array(params_list)


def generate_params_4_array(elements_tuple: tuple[str, ...]) -> ndarray:
    """
    构建计算用的描述符矩阵(用于特殊的四个描述符)

    elements_tuple: 六种需要计算的元素名
    elements_tuple type: tuple[str, ...]

    rtype: ndarray
    """
    params_list: list[list[float]] = []
    for element in elements_tuple:
        params_list.append(params_4_dict[element]["params"])
    return np.array(params_list)


def con_to_array(con_tuple: tuple[float, ...]) -> ndarray:
    """将成分组成转换为nparray

    Args:
        con_tuple (tuple[int, ...]): 成分组成

    Returns:
        ndarray: (x,)
    """
    return np.array(con_tuple)


def make_ave_params(ave_array: ndarray) -> ndarray:
    """
    将ave_array转化为后续其他计算需要的shape

    ave_array: calc_ave计算的结果，(x,)
    ave_array type: ndarray

    return: (1,x)
    rtype: ndarray
    """
    return ave_array.reshape(1, -1).T


def calc_ave(con_array: ndarray, params_array: ndarray) -> ndarray:
    """计算平均值

    Args:
        con_array (tuple[int, ...]): 元素的组成
        params_array: 描述符矩阵

    Returns:
        ndarray:
    """
    return (params_array * con_array).sum(axis=1) / con_array.sum()


def calc_rmse(
    con_array: ndarray, ave_params: ndarray, params_array: ndarray
) -> ndarray:
    """计算均方根误差

    Args:
        con_array (tuple[int, ...]): 元素组成
        ave_params (ndarray): 已计算的均值，(x, 1)
        params_array: 描述符矩阵

    Returns:
        ndarray: (x,)
    """

    return np.sqrt((((1 - (params_array / ave_params)) ** 2) * con_array).sum(axis=1))


def calc_range(
    con_array: ndarray, ave_params: ndarray, params_array: ndarray
) -> ndarray:
    """计算极差

    Args:
        con_array (tuple[int, ...]): 元素组成
        ave_params (ndarray): 已计算的均值，(x, 1)
        params_array: 描述符矩阵

    Returns:
        ndarray: (x,)
    """
    temp_array = ((1 - (params_array / ave_params)) ** 2) * con_array
    return temp_array.max(axis=1) - temp_array.min(axis=1)


def calc_pair(con_array: ndarray, params_array: ndarray) -> ndarray:
    """计算PairsF*，包含i=j的情况

    Args:
        con_array (ndarray): 元素组成
        params_array: 描述符矩阵

    Returns:
        ndarray: (x,)
    """
    cifi: ndarray = params_array * con_array

    sum_cicjfij: ndarray = np.zeros((params_array.shape[0],))
    for i in range(con_array.shape[0]):
        for j in range(i, con_array.shape[0]):
            sum_cicjfij += (
                ((cifi[:, i] + cifi[:, j]) / (con_array[i] + con_array[j]))
                * con_array[i]
                * con_array[j]
            )

    sum_cij: ndarray = (np.sum(con_array) ** 2 + np.sum(con_array**2)) / 2

    return sum_cicjfij / sum_cij


def calc_Smix(con_array: ndarray) -> float:
    """计算混合熵

    Args:
        con_array (ndarray): 元素组成

    Returns:
        float:
    """
    log_con_array: ndarray = np.log(con_array)
    return float((con_array * log_con_array).sum() * (-8.314))


def calc_lambda(Smix_data: float, rmse_r: float) -> float:
    # RMSE_R是原子半径错配，是第32个元素性质的均方根误差
    # 所以RMSE_R可在函数外进行赋值，然后作为参数导入？
    return Smix_data / rmse_r**2


def calc_gamma(params_array: ndarray, ave_r: float) -> float:
    # γ是拓扑原子半径错配，基于第32个元素性质，需要搜索到最大半径和最小半径
    # R是原子半径均值，是第32个元素性质的均值
    Min_R: float = params_array[29, :].min(axis=0)
    Max_R: float = params_array[29, :].max(axis=0)
    W_S: float = (
        1 - (((Max_R + ave_r) ** 2 - ave_r**2) / (Max_R + ave_r) ** 2) ** 0.5
    )  # S,small，小原子拓扑
    W_L: float = (
        1 - (((Min_R + ave_r) ** 2 - ave_r**2) / (Min_R + ave_r) ** 2) ** 0.5
    )  # L,large，大原子拓扑
    return W_S / W_L


def calc_Ev(con_array: ndarray, params_array: ndarray) -> float:
    Ev: float = 0
    i: int
    j: int
    for i in range(con_array.shape[0]):
        for j in range(i + 1, con_array.shape[0]):
            VA: float = params_array[19, i]  # 摩尔体积,第22个元素性质
            VB: float = params_array[19, j]  # 摩尔体积
            HA: float = (
                96.48532797 * params_array[41, i]
            )  # 单元素的空位形成能,第44个元素性质，96.48532797为单位换算
            HB: float = 96.48532797 * params_array[41, j]  # 单元素的空位形成能
            xA: float = con_array[i]  # 成分
            xB: float = con_array[j]  # 成分
            CB: float = xB * VB ** (2 / 3) / (xA * VA ** (2 / 3) + xB * VB ** (2 / 3))
            CA: float = xA * VA ** (2 / 3) / (xA * VA ** (2 / 3) + xB * VB ** (2 / 3))
            fAB: float
            HAB: float
            if VA > VB:
                fAB = CB * (1 + 5 * (CA * CB) ** 2)
                HAB = (1 - fAB) * HB + fAB * HA * (VB / VA) ** (5 / 6)
            else:
                fAB = CA * (1 + 5 * (CA * CB) ** 2)
                HAB = (1 - fAB) * HA + fAB * HB * (VA / VB) ** (5 / 6)
            Ev = Ev + HAB * xB * xA
    Ev = Ev * 4 / 96.48532797  # 应该直接算出来就是千焦每摩尔的单位
    return Ev


def calc_G_G0(G: float, G0: float) -> float:
    return G / G0


def calc_K_G(K: float, G: float) -> float:
    return K / G


def calc_Tb_Tm(Tb: float, Tm: float) -> float:
    return Tb - Tm


def calc_Hmix(con_array: ndarray, Hmix_con: ndarray) -> float:
    cicj: ndarray = con_array[:, None] * con_array[None, :]
    cicjHmix: ndarray = cicj * Hmix_con
    return cicjHmix.sum() * 2


def calc_rmse_Hmix(con_array: ndarray, Hmix_data: float, Hmix_con: ndarray) -> float:
    if Hmix_data == 0:
        return 0
    cicj: ndarray = con_array[:, None] * con_array[None, :]
    cicjRmseHmix: ndarray = cicj * (1 - Hmix_con / Hmix_data) ** 2
    mask: ndarray = np.zeros_like(cicjRmseHmix, dtype=bool)
    mask[np.triu_indices_from(mask, k=1)] = True
    upper_right_triangle: ndarray = cicjRmseHmix[mask]
    return (upper_right_triangle.sum()) ** 0.5


def calc_reciprocal_omega(Smix_data: float, Hmix_data: float, Tm: float) -> float:
    # Tm是熔点，是第37个元素性质的均值
    # 所以Tm可在函数外进行赋值，然后作为参数导入？
    return abs(Hmix_data) / (0.001 * Tm * Smix_data)


def calc_params_WEF(con_array: ndarray, WEF_con: ndarray) -> tuple[float, ...]:
    ave_WEF: float = ((WEF_con * con_array).sum() / con_array.sum()) ** 6
    rmse_WEF: float = (((1 - ((WEF_con**6) / ave_WEF)) ** 2) * con_array).sum() ** 0.5
    temp_range_array: ndarray = ((1 - ((WEF_con**6) / ave_WEF)) ** 2) * con_array
    range_WEF: float = temp_range_array.max() - temp_range_array.min()

    # pair_WEF
    cifi: ndarray = (WEF_con**6) * con_array
    sum_cicjfij: float = 0
    sum_cicj: float = 0
    for i in range(con_array.shape[0]):
        for j in range(i, con_array.shape[0]):
            sum_cicjfij += (
                ((cifi[i] + cifi[j]) / (con_array[i] + con_array[j]))
                * con_array[i]
                * con_array[j]
            )
            sum_cicj += con_array[i] * con_array[j]
    pair_WEF: float = sum_cicjfij / sum_cicj

    return ave_WEF, rmse_WEF, range_WEF, pair_WEF


def calc_have_zero(
    con_array: ndarray, params_array_with_zero: ndarray
) -> tuple[float, ...]:
    """
    对于可能全零行计算各种描述符

    con_array: 六种元素组分
    con_array type: ndarray
    params_array_with_zero: 可能为全零的一行
    params_array_with_zero type: ndarray

    rtype: tuple[float, ...]
    """
    ave_with_zero: float = (params_array_with_zero * con_array).sum() / con_array.sum()
    rmse_with_zero: float
    range_with_zero: float
    if ave_with_zero == 0:
        rmse_with_zero = 0
        range_with_zero = 0
    else:
        temp_range_array: ndarray = (
            (1 - (params_array_with_zero / ave_with_zero)) ** 2
        ) * con_array
        rmse_with_zero = temp_range_array.sum() ** 0.5
        range_with_zero = temp_range_array.max() - temp_range_array.min()

    # pair_with_zero
    cifi: ndarray = params_array_with_zero * con_array
    sum_cicjfij: float = 0
    sum_cicj: float = 0
    for i in range(con_array.shape[0]):
        for j in range(i, con_array.shape[0]):
            sum_cicjfij += (
                ((cifi[i] + cifi[j]) / (con_array[i] + con_array[j]))
                * con_array[i]
                * con_array[j]
            )
            sum_cicj += con_array[i] * con_array[j]
    pair_with_zero: float = sum_cicjfij / sum_cicj

    return ave_with_zero, rmse_with_zero, range_with_zero, pair_with_zero
