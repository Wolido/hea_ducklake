# Minimal Reproducible HEA Framework Workflow

This is a minimal end-to-end example that reproduces the integrated framework
used to build `hea_ducklake`. It demonstrates both core components described in
the paper:

1. **Stateless parallel computation** for descriptor generation.
2. **Lakehouse-based data management** for storage and access.

The example uses:

- a local Redis instance for task distribution,
- the existing `calc_descriptors/calc_py` calculation code,
- one or more Python workers,
- a collector that writes results to CSV,
- conversion of the CSV to compressed Parquet,
- a local MinIO instance as an S3-compatible object store,
- a DuckDB metadata catalog that points to the remote Parquet file,
- SQL queries through the metadata catalog.

The computation is intentionally small (100 compositions from the first
6-element family) so that it can be run on a laptop in seconds.

## What this example demonstrates

1. **Task generation** — how HEA compositions are turned into calculation tasks,
   using the same Rust routine (`rs_calc_faster.rs_que_push_iter`) as the full
   production pipeline.
2. **Distributed execution** — tasks are pushed to Redis and picked up by
   stateless workers.
3. **Descriptor computation** — each worker calls `calc_main_progress()` from
   `calc_descriptors/calc_py`.
4. **Result collection** — computed descriptors are written to a CSV file.
5. **Lakehouse storage** — the CSV is converted to a compressed Parquet file and
   uploaded to MinIO (S3-compatible storage).
6. **Metadata catalog** — a small DuckDB catalog is created that records the
   location of the Parquet object.
7. **Data access** — the dataset is queried through the metadata catalog with
   DuckDB SQL, without downloading the full Parquet file.

For production-scale computation (trillion-scale descriptors), scale out the
workers and use [IDM-GridCore](https://github.com/Wolido/idm-gridcore) to
manage heterogeneous compute nodes.

## Prerequisites

- Python 3.10+
- Rust toolchain (`cargo` / `rustup`)
- `maturin`: `pip install maturin`
- Docker / Docker Compose (for Redis and MinIO)
- Python packages: `redis`, `numpy`, `pandas`, `duckdb`, `pyarrow`, `minio`

> **Tip:** Create a virtual environment for this example so its dependencies do
> not conflict with other projects in your global Python installation.
>
> ```bash
> python3 -m venv venv
> source venv/bin/activate  # On Windows: venv\Scripts\activate
> pip install -r requirements.txt
> ```

## Setup

### 1. Install Rust

The example uses the same Rust/PyO3 extension (`rs_calc_faster`) as the
production pipeline. If Rust is not already installed:

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

Verify the installation:

```bash
rustc --version
cargo --version
```

### 2. Install maturin

```bash
pip install maturin
```

### 3. Compile the Rust extension

```bash
cd ../../calc_descriptors/calc_faster_rs
maturin develop --release
```

This command builds `rs_calc_faster` and installs it into the current Python
environment. It is the same extension used by `calc_descriptors/calc_py/main.py`
in the full pipeline.

### 4. Install Python dependencies

```bash
cd ../../examples/minimal_workflow
pip install -r requirements.txt
```

## Run

Open terminals and run each step in order.

### 1. Start Redis and MinIO

```bash
docker compose up -d
```

This starts:

- Redis on `localhost:6380`
- MinIO S3 API on `localhost:9000`
- MinIO console on `localhost:9001`

> **Troubleshooting:** If Docker Hub is unreachable in your region and the
> MinIO image cannot be pulled, you can install MinIO locally via Homebrew:
>
> ```bash
> brew install minio
> export MINIO_ROOT_USER=minioadmin
> export MINIO_ROOT_PASSWORD=minioadmin
> minio server /tmp/minio_data --address :9000 --console-address :9001
> ```
>
> Then keep `MINIO_ENDPOINT=localhost:9000` in the following steps.

### 2. Generate tasks

```bash
python generate_tasks.py
```

This generates all composition tasks for the first 6-element family using the
same Rust routine as the full pipeline (`rs_calc_faster.rs_que_push_iter`) and
pushes the first 100 tasks to the Redis queue `hea:minimal:input`.

### 3. Run the worker

```bash
python worker.py
```

You can start multiple workers in separate terminals to parallelize the
computation.

### 4. Collect results

```bash
python collect_results.py
```

This drains the output queue `hea:minimal:output` and writes `results.csv`.

### 5. Convert to Parquet

```bash
python convert_to_parquet.py
```

This converts `results.csv` into `results.parquet` using the Zstandard
compression codec.

Optionally, query the local Parquet file before uploading:

```bash
python query_parquet.py
```

This runs DuckDB SQL directly on `results.parquet` and is useful for quick
checks before uploading the data to MinIO.

### 6. Upload Parquet to MinIO (S3-compatible storage)

```bash
python upload_to_minio.py
```

This uploads `results.parquet` to the local MinIO bucket `hea-minimal`,
demonstrating the S3-compatible object-storage layer.

### 7. Create the DuckDB metadata catalog

```bash
python create_metadata.py
```

This creates `metadata.duckdb`, a small catalog file that records the S3
location of the Parquet object. In the full `hea_ducklake` database, users
download a similarly small metadata file to access the entire dataset.

> **Note:** The first time DuckDB needs the `httpfs` extension it will download
> it from the DuckDB extension repository. Make sure the machine has internet
> access for this step, or install the extension manually beforehand.

### 8. Query through the metadata catalog

```bash
python query_via_metadata.py
```

This runs DuckDB SQL queries through `metadata.duckdb` without importing the
full Parquet file locally.

You can also open the catalog interactively:

```bash
duckdb metadata.duckdb
```

Then run:

```sql
SELECT con_index, ave_0 FROM results LIMIT 5;
```

## Expected output

- `results.csv` — 100 rows of HEA descriptors.
- `results.parquet` — compressed columnar version of the CSV.
- `metadata.duckdb` — small DuckDB catalog pointing to the S3/MinIO object.

The column names in `results.csv` follow the same convention used in the full
`hea_ducklake` descriptor tables.

## Configuration

All scripts read the following environment variables:

| Variable | Default |
|---|---|
| `REDIS_URL` | `redis://localhost:6380` |
| `INPUT_QUEUE` | `hea:minimal:input` |
| `OUTPUT_QUEUE` | `hea:minimal:output` |
| `TOTAL_TASKS` | `100` |
| `OUTPUT_CSV` | `results.csv` |
| `OUTPUT_PARQUET` | `results.parquet` |
| `MINIO_ENDPOINT` | `localhost:9000` |
| `MINIO_REGION` | `us-east-1` |
| `MINIO_ACCESS_KEY` | `minioadmin` |
| `MINIO_SECRET_KEY` | `minioadmin` |
| `MINIO_BUCKET` | `hea-minimal` |
| `MINIO_OBJECT` | `results.parquet` |
| `METADATA_PATH` | `metadata.duckdb` |

For example, to generate 1,000 tasks:

```bash
TOTAL_TASKS=1000 python generate_tasks.py
```

## Extending to the full database

To build the full 17.5 TB database shown in the paper:

1. Generate all 6-element combinations and all valid compositions.
2. Push them to Redis in batches.
3. Run many workers (on servers, workstations, or edge devices) via
   [IDM-GridCore](https://github.com/Wolido/idm-gridcore).
4. Write results directly to Parquet files organized by element family.
5. Upload the Parquet files to an S3-compatible object store.
6. Generate DuckDB metadata catalogs so users can query the full database
   without downloading it.

This minimal workflow contains the same core logic, just scaled down for
demonstration and testing.
