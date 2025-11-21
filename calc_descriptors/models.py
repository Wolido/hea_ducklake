from dataclasses import dataclass

@dataclass
class CALCDATA:
    con_index: int
    elem_index: int
    ave_array_list: list
    rmse_array_list: list
    range_array_list: list
    pair_array_list: list
    Smix_data: float
    lambda_data: float
    gamma_data: float
    Ev_data: float
    GG0_data: float
    KG_data: float
    TbTm_data: float
    Hmix_data: float
    rmse_Hmix_data: float
    omega_data: float


@dataclass
class CONDATA:
    con_index: int
    elem_index: int
    con1: float
    con2: float
    con3: float
    con4: float
    con5: float
    con6: float
    elem1: str
    elem2: str
    elem3: str
    elem4: str
    elem5: str
    elem6: str