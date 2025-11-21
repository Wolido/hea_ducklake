use core::panic;
use serde_json::to_string;
use serde_json::Number;
use serde_json::Value;
use std::collections::HashMap;

use pyo3::prelude::*;

const MIX_H: [[i32; 15]; 15] = [
    [
        0, -2, 0, -11, -1, 13, -1, -5, -17, -16, -15, 0, -7, -25, -21,
    ],
    [
        -2, 0, -8, -22, -7, 4, 0, -7, -35, -30, -29, -3, -18, -49, -42,
    ],
    [0, -8, 0, -19, 2, 4, -5, 5, -8, -4, -4, 6, -1, -15, -12],
    [
        -11, -22, -19, 0, -10, -1, -19, -5, -30, -18, -19, -2, -16, -44, -39,
    ],
    [-1, -7, 2, -10, 0, 12, -4, 0, -7, -7, -7, 1, -2, -12, -9],
    [13, 4, 4, -1, 12, 0, 6, 19, -9, 3, 2, 22, 5, -23, -17],
    [
        -1, 0, -5, -19, -4, 6, 0, -5, -28, -25, -24, -1, -14, -41, -35,
    ],
    [-5, -7, 5, -5, 0, 19, -5, 0, -4, -6, -5, 0, 0, -6, -4],
    [-17, -35, -8, -30, -7, -9, -28, -4, 0, 2, 1, -6, -2, 0, 0],
    [-16, -30, -4, -18, -7, 3, -25, -6, 2, 0, 0, -8, -1, 4, 4],
    [-15, -29, -4, -19, -7, 2, -24, -5, 1, 0, 0, -7, -1, 3, 3],
    [0, -3, 6, -2, 1, 22, -1, 0, -6, -8, -7, 0, -1, -9, -6],
    [-7, -18, -1, -16, -2, 5, -14, 0, -2, -1, -1, -1, 0, -4, -2],
    [-25, -49, -15, -44, -12, -23, -41, -6, 0, 4, 3, -9, -4, 0, 0],
    [-21, -42, -12, -39, -9, -17, -35, -4, 0, 4, 3, -6, -2, 0, 0],
];

fn generate_elem_index_map() -> HashMap<String, usize> {
    let mut elem_index_map: HashMap<String, usize> = HashMap::new();
    let elem_list = [
        "Fe", "Ni", "Mn", "Al", "Cr", "Cu", "Co", "Mo", "Ti", "Nb", "Ta", "W", "V", "Zr", "Hf",
    ];
    for (index, elem) in elem_list.iter().enumerate() {
        elem_index_map.insert(elem.to_string(), index);
    }
    elem_index_map
}

#[pyfunction]
fn rs_generate_hmix_con(elem_tuple: Vec<String>) -> PyResult<Vec<Vec<i32>>> {
    let mut elem_index_list = Vec::new();
    let elem_index_map = generate_elem_index_map();
    for elem in elem_tuple {
        match elem_index_map.get(&elem) {
            Some(&index) => elem_index_list.push(index),
            None => panic!("元素名称错误!"),
        };
    }
    let mut hmix_con: Vec<Vec<i32>> = vec![vec![0; 6]; 6];
    for (i, num1) in elem_index_list.iter().enumerate() {
        for (j, num2) in elem_index_list.iter().enumerate() {
            hmix_con[i][j] = MIX_H[*num1][*num2]
        }
    }
    Ok(hmix_con)
}

#[pyfunction]
fn rs_que_push_iter(
    elem_index: u32,
    elem_tuple: Vec<String>,
    con_list: Vec<Vec<u32>>,
) -> PyResult<Vec<String>> {
    let mut result_vec = vec!["".to_string(); con_list.len()];
    for (con_index, con_iter) in con_list.iter().enumerate() {
        let mut result_map = HashMap::new();
        result_map.insert(
            "con_index".to_string(),
            Value::Number((con_index + 1).into()),
        );
        result_map.insert(
            "elem_index".to_string(),
            Value::Number((elem_index + 1).into()),
        );
        result_map.insert(
            "con1".to_string(),
            Value::Number(Number::from_f64((con_iter[0] as f64) / 100.0).unwrap()),
        );
        result_map.insert(
            "con2".to_string(),
            Value::Number(Number::from_f64((con_iter[1] as f64) / 100.0).unwrap()),
        );
        result_map.insert(
            "con3".to_string(),
            Value::Number(Number::from_f64((con_iter[2] as f64) / 100.0).unwrap()),
        );
        result_map.insert(
            "con4".to_string(),
            Value::Number(Number::from_f64((con_iter[3] as f64) / 100.0).unwrap()),
        );
        result_map.insert(
            "con5".to_string(),
            Value::Number(Number::from_f64((con_iter[4] as f64) / 100.0).unwrap()),
        );
        result_map.insert(
            "con6".to_string(),
            Value::Number(Number::from_f64((con_iter[5] as f64) / 100.0).unwrap()),
        );
        result_map.insert(
            "elem1".to_string(),
            Value::String(elem_tuple[0].to_string()),
        );
        result_map.insert(
            "elem2".to_string(),
            Value::String(elem_tuple[1].to_string()),
        );
        result_map.insert(
            "elem3".to_string(),
            Value::String(elem_tuple[2].to_string()),
        );
        result_map.insert(
            "elem4".to_string(),
            Value::String(elem_tuple[3].to_string()),
        );
        result_map.insert(
            "elem5".to_string(),
            Value::String(elem_tuple[4].to_string()),
        );
        result_map.insert(
            "elem6".to_string(),
            Value::String(elem_tuple[5].to_string()),
        );

        result_vec[con_index] = to_string(&result_map).unwrap()
    }
    Ok(result_vec)
}

#[pyfunction]
fn rs_generate_con_list_all() -> PyResult<Vec<[i32; 6]>> {
    let mut result_vec: Vec<[i32; 6]> = Vec::new();
    for it1 in 5..=35 {
        for it2 in 5..=35 {
            for it3 in 5..=35 {
                for it4 in 5..=35 {
                    for it5 in 5..=35 {
                        let it_sum = it1 + it2 + it3 + it4 + it5;
                        if (it_sum <= 95) && (it_sum >= 65) {
                            let con6 = 100 - it_sum;
                            result_vec.push([it1, it2, it3, it4, it5, con6]);
                        }
                    }
                }
            }
        }
    }
    Ok(result_vec)
}

#[pyfunction]
fn rs_calc_ev(con_list: Vec<f64>, params_list: Vec<Vec<f64>>) -> PyResult<f64> {
    let mut ev: f64 = 0.0;
    for i in 0..con_list.len() {
        for j in i + 1..con_list.len() {
            let va = params_list[19][i];
            let vb = params_list[19][j];
            let ha = params_list[41][i] * 96.48532797;
            let hb = params_list[41][j] * 96.48532797;
            let xa = con_list[i];
            let xb = con_list[j];
            let cb = xb * vb.powf(2.0 / 3.0) / (xa * va.powf(2.0 / 3.0) + xb * vb.powf(2.0 / 3.0));
            let ca = xa * va.powf(2.0 / 3.0) / (xa * va.powf(2.0 / 3.0) + xb * vb.powf(2.0 / 3.0));
            let fab;
            let hab;
            if va > vb {
                fab = cb * (1.0 + 5.0 * (ca * cb).powf(2.0));
                hab = (1.0 - fab) * hb + fab * ha * (vb / va).powf(5.0 / 6.0);
            } else {
                fab = ca * (1.0 + 5.0 * (ca * cb).powf(2.0));
                hab = (1.0 - fab) * ha + fab * hb * (va / vb).powf(5.0 / 6.0);
            }
            ev += hab * xb * xa;
        }
    }
    ev = ev * 4.0 / 96.48532797;
    Ok(ev)
}

#[pyfunction]
fn rs_round_array(array: Vec<f64>) -> PyResult<Vec<f64>> {
    let mut return_array = Vec::new();
    for number in array.iter() {
        return_array.push((number * 10000.0).round() / 10000.0)
    }
    Ok(return_array)
}

/// A Python module implemented in Rust.
#[pymodule]
fn rs_calc_faster(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(rs_generate_hmix_con, m)?)?;
    m.add_function(wrap_pyfunction!(rs_que_push_iter, m)?)?;
    m.add_function(wrap_pyfunction!(rs_generate_con_list_all, m)?)?;
    m.add_function(wrap_pyfunction!(rs_calc_ev, m)?)?;
    m.add_function(wrap_pyfunction!(rs_round_array, m)?)?;
    Ok(())
}
