# Query Case Results of the HEA Database

This folder contains the benchmark screenshots used in the *Nature Communications* submission. Each figure compares the performance of querying the HEA database through different backends: **PostgreSQL**, **DuckLake** (DuckDB over S3-compatible object storage), and raw **CSV**.

---

## Side-by-side comparison: full-table queries

### Fig. 1 — DuckLake: Querying the entire composition dataset

Querying all rows of `hea_con_6` (≈10.76 M rows, 7 columns) through the DuckLake lakehouse. **Elapsed time: 67.724 s (≈1 min 7 s).**

![Fig. 1](docs/query_case_results/assets/fig_01.png)

### Fig. 2 — PostgreSQL: Querying the entire descriptor table

Querying all rows of `hea_6_c_1921` (≈10.76 M rows, 195 columns) via PostgreSQL. **Elapsed time: 00:26:25.83.**

![Fig. 2](docs/query_case_results/assets/fig_02.png)

---

## PostgreSQL

### Fig. 3 — Querying four columns in one HEA family

Projection query (`con_index, ave_fe1, rmse_ft2, range_fp5`) on `hea_6_c_128` (≈10.76 M rows) via PostgreSQL. **Elapsed time: 00:01:13.42.**

![Fig. 3](docs/query_case_results/assets/fig_03.png)

### Fig. 4 — Reverse query by descriptor values

Reverse lookup of compositions in `hea_6_c_192` joined with `hea_con_6`, filtered by descriptor thresholds, via PostgreSQL. **Elapsed time: 00:02:19.08.**

![Fig. 4](docs/query_case_results/assets/fig_04.png)

---

## DuckLake

### Fig. 5 — Querying the entire composition dataset

Querying all rows of `hea_con_6` (≈10.76 M rows, 7 columns) through the DuckLake lakehouse. **Elapsed time: 00:00:04.72.**

![Fig. 5](docs/query_case_results/assets/fig_05.png)

### Fig. 6 — Querying a full Parquet file of one HEA family

Full-table query on `hea_6_c_1921` (194 descriptors) via DuckLake. **Elapsed time: 00:04:41.29.**

![Fig. 6](docs/query_case_results/assets/fig_06.png)

### Fig. 7 — Querying four columns in one HEA family

Same projection as Fig. 3 (`con_index, ave_fe1, rmse_ft2, range_fp5`) via DuckLake. **Elapsed time: 00:00:08.86.**

![Fig. 7](docs/query_case_results/assets/fig_07.png)

### Fig. 8 — Reverse query by descriptor values

Same reverse lookup as Fig. 4 via DuckLake. **Elapsed time: 00:00:08.99.**

![Fig. 8](docs/query_case_results/assets/fig_08.png)

---

## CSV

### Fig. 9 — Querying the entire composition dataset

Attempting to query the entire composition dataset from CSV. The process failed with an out-of-memory error (`Failed to allocate segment ... out of space`) after **~1440.65 s** of real time.

![Fig. 9](docs/query_case_results/assets/fig_09.png)

### Fig. 10 — Querying a full Parquet-derived CSV of one HEA family

Querying the CSV equivalent of a single HEA family (194 descriptors). **Elapsed time: 40.88 s.**

![Fig. 10](docs/query_case_results/assets/fig_10.png)

### Fig. 11 — Querying four columns from CSV

Attempting the four-column projection from CSV. The process ran out of memory after **~1405.22 s** of real time.

![Fig. 11](docs/query_case_results/assets/fig_11.png)

### Fig. 12 — Reverse query by descriptor values from CSV

Attempting the reverse lookup from CSV. The process ran out of memory after **~1328.10 s** of real time.

![Fig. 12](docs/query_case_results/assets/fig_12.png)

---

## Cross-family reverse query via DuckLake

### Fig. 13 — Persistent DuckDB connection

Reverse query of alloy compositions across all **5,005 HEA families** by descriptor values, keeping a single persistent DuckDB connection. **Elapsed time: 00:03:27.94.**

![Fig. 13](docs/query_case_results/assets/fig_13.png)

### Fig. 14 — Reconnecting every 100 Parquet files

Same cross-family reverse query, but releasing and re-establishing the DuckDB connection after every 100 Parquet files. **Elapsed time: 00:07:39.80.**

![Fig. 14](docs/query_case_results/assets/fig_14.png)
