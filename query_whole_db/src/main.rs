use duckdb::{params, Connection};
use csv::Writer;
use anyhow::Result;
use std::fs::File;
use indicatif::{ProgressBar, ProgressStyle};

fn main() -> Result<()> {
    let conn = Connection::open_in_memory()?;

    conn.execute("SET s3_endpoint='IPAddress:Port';", [])?;
    conn.execute("SET s3_url_style='path';", [])?;
    conn.execute("SET s3_use_ssl='false';", [])?;

    conn.execute(
        r#"
        ATTACH 'ducklake:metadata.ducklake' as hea (
            DATA_PATH 's3://idmdatabase/hea'
        );
        "#,
        [],
    )?;
    conn.execute("USE hea;", [])?;

    let mut whole_results: Vec<Vec<String>> = Vec::new();

    let pb = ProgressBar::new(5005);
    pb.set_style(
        ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta})")?
            .progress_chars("#>-")
    );
    pb.set_message("Query is running...");

    for i in 1..=5005 {
        let query = format!(
            r#"
            SELECT hea_con_6.con1, hea_con_6.con2, hea_con_6.con3, hea_con_6.con4, hea_con_6.con5, hea_con_6.con6
            FROM hea_6_c_{}
                     LEFT JOIN hea_con_6 ON hea_6_c_{}.con_index = hea_con_6.id
            WHERE ave_fe1 > 1.68
              AND pair_fe5 > 7.80
              AND gg0_data > 0.87
              AND tbtm_data > 1732
              AND rmse_hmix_data < 0.39;
            "#,
            i, i
        );

        let mut stmt = conn.prepare(&query)?;
        let result_iter = stmt.query_map([], |row| {
            Ok((
                row.get::<usize, f64>(0)?,
                row.get::<usize, f64>(1)?,
                row.get::<usize, f64>(2)?,
                row.get::<usize, f64>(3)?,
                row.get::<usize, f64>(4)?,
                row.get::<usize, f64>(5)?,
            ))
        })?;

        let mut result_list: Vec<(f64, f64, f64, f64, f64, f64)> = Vec::new();
        for tuple_res in result_iter {
            if let Ok(t) = tuple_res {
                result_list.push(t);
            }
        }

        if !result_list.is_empty() {
            let elem_query = "SELECT elem1, elem2, elem3, elem4, elem5, elem6 FROM hea_elements_6 WHERE id = ?;";
            let mut elem_stmt = conn.prepare(elem_query)?;
            let elements: (String, String, String, String, String, String) = elem_stmt.query_row(params![i], |row| {
                Ok((
                    row.get::<usize, String>(0)?,
                    row.get::<usize, String>(1)?,
                    row.get::<usize, String>(2)?,
                    row.get::<usize, String>(3)?,
                    row.get::<usize, String>(4)?,
                    row.get::<usize, String>(5)?,
                ))
            })?;

            for result in result_list {
                let mut row: Vec<String> = Vec::new();
                row.push(format!("{:.2}", result.0));
                row.push(format!("{:.2}", result.1));
                row.push(format!("{:.2}", result.2));
                row.push(format!("{:.2}", result.3));
                row.push(format!("{:.2}", result.4));
                row.push(format!("{:.2}", result.5));
                row.push(elements.0.clone());
                row.push(elements.1.clone());
                row.push(elements.2.clone());
                row.push(elements.3.clone());
                row.push(elements.4.clone());
                row.push(elements.5.clone());
                whole_results.push(row);
            }
        }

        pb.inc(1);
    }

    pb.finish_with_message("Query is finished.");

    let file = File::create("./query_result.csv")?;
    let mut wtr = Writer::from_writer(file);
    wtr.write_record(&[
        "con1", "con2", "con3", "con4", "con5", "con6",
        "elem1", "elem2", "elem3", "elem4", "elem5", "elem6"
    ])?;
    for result in whole_results {
        wtr.write_record(&result)?;
    }
    wtr.flush()?;

    Ok(())
}

