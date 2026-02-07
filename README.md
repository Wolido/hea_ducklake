<img src="https://disc-wolido.oss-cn-beijing.aliyuncs.com/idm-logo/%E6%B5%85%E8%89%B2%E8%83%8C%E6%99%AFlogo-%E5%B7%A6%E5%8F%B3.png" style="height: 60px" />

- [中文](README_zh.md)
- [English](README.md)

---

## 🚀 AI Agent Skill Available!

**Query this database effortlessly using AI agents with our dedicated skill:**

👉 **[agent-hea6-ducklake](https://github.com/Wolido/agent-hea6-ducklake)** 👈

*No SQL required - just ask questions in natural language!*

---

# HEA DuckLake

This project includes a foundational database for six principal elements high-entropy alloys, suitable for computations, ML training and predictions based on high-entropy alloys.

The data is distributed in the form of DuckLake's lakehouse. The project contains DuckLake's metadata files as well as an `init.sql` file for accessing the data lakehouse.

The actual total data volume of the project is 17.5TB. Thanks to DuckLake's lakehouse technology, you only need to download tens of megabytes of metadata to remotely access the entire database.

There are two accessible data lakehouses in the project: one is the descriptors for high-entropy alloys under the `descriptor` path, and the other is a set of ML model prediction results under the pred_demo path. Files ending with `.ducklake` are metadata files for the lakehouse.

The descriptor lakehouse contains a table of element combinations named `hea_elements_6`; a table of element composition ratios named `hea_con_6`; and an explanation table for descriptor field names named `descriptor_names`. These tables can help you better understand and use the lakehouse when querying the descriptor tables. The naming format for the descriptor data tables is `hea_6_c_x`, where `x` is the index of the element combination in the `hea_elements_6` table.

The naming format for the tables in the prediction data lakehouse is `pred_x`, where `x` is the index of the element combination in the `hea_elements_6` table of the descriptor lakehouse.

## Usage: Taking the metadata under the descriptors path as an example

### Quick Start

Click the Binder link to start running the demo: [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/Wolido/hea_ducklake/run_demo?urlpath=%2Fdoc%2Ftree%2Frun_demo%2Fmain.ipynb)

The example contains two Jupyter Notebook files:
- `main.ipynb`: contains some basic data query examples
- `some_big_query.ipynb`: contains examples that take longer to execute

Due to Git repository limitations that prevent uploading very large files, metadata cannot be stored in SQLite format. Additionally, the DuckLake format metadata does not support multiple concurrent connections.

Therefore, when running `some_big_query.ipynb`, **please make sure to close the `main.ipynb` notebook first**, otherwise the third cell will throw an error.

### Through DuckDB

- Install DuckDB Command Line Client: Visit the following website to install the CLI program https://duckdb.org/install

- Install the ducklake plugin: Run `INSTALL ducklake;` in the DuckDB CLI

- Run `duckdb --init init.sql` under the descriptors path to establish connection with the lakehouse

- Use SQL to query data within the lakehouse

### Through Python

- Install the Python library duckdb: `pip install duckdb`, or use the `uv sync` command to sync dependencies. The project includes `pyproject.toml` and `uv.lock` files.

- Subsequent operation steps refer to the `use_descriptors.py` script.

## Demo

The database referenced by the `metadata.ducklake` file under the descriptors path contains a total of 5008 tables, of which 5005 are descriptors for six principal elements high-entropy alloys. Each table has 195 columns and over 10 million rows, stored in a compressed columnar format, requiring approximately more than 4GB of space. However, most queries do not require the full dataset, so query results can be returned very quickly. The following are two examples, both using SQL operations.

### Query of the  element components of six principal elements high-entropy alloys using descriptors

In a single city, queries on the public network can return results in as fast as 2 seconds. If there have been prior queries about this table, caching could make the query speed even faster. Previously, cross-city query speeds were around 4 seconds. In scenarios like cross-country or cross-continent, the speed might be a bit slower, but still fast enough.

<img src="./demo-pics/qc.png" style="height: 200px" />

### Query on certain columns in the data table

Thanks to column storage technology, non-full-table queries do not require transmitting all data over the network. Full table queries on the descriptor table take on the order of minutes, depending on network conditions; we have measured speeds such as 2 minutes and 7 minutes.

Queries on the con_index column and the other three descriptors are much faster, taking about 10 seconds, with most of the time spent transmitting the 10 million × 4 data back over the network.

<img src="./demo-pics/qd1.png" style="height: 200px" />

...

<img src="./demo-pics/qd2.png" style="height: 200px">

### Full database query

Similar to the previous example, use descriptors to query combinations of high-entropy alloys, but this time querying the entire database. This query example is written in Rust, with the code located in the `query_whole_db` path.

Querying in a public network environment is costly and limited by network speed, so we completed this query in an internal network environment. For a database containing a total of 50 billion combinations, the full database query only took 3 minutes and 22 seconds.

<img src="./demo-pics/query_whole_db_2.png" style="height: 100px">

By sacrificing some time, the full database query can run smoothly on a machine with 4G memory. We ran the program on a 4-core 4G virtual machine, resetting the database connection every 100 tables queried, and it ultimately took 7 minutes and 38 seconds.

<img src="demo-pics/query_4g.png" style="height: 100px">

Such performance ensures that any PC can smoothly complete the full database query.

### Edge Device Query Test

We conducted data query tests on a Raspberry Pi 5 with 4GB of RAM.

<img src="demo-pics/raspi5.png" style="height: 200px">

Due to the excessively large size of individual tables, querying an entire table on the Raspberry Pi 5 triggers an OOM error. Even after compression, a single table already exceeds the available memory of the Raspberry Pi 5.

However, performance on all other queries was exceptionally strong. For example, retrieving the first 100 rows of all columns from a table completes within 10 seconds. This is a query pattern that cannot fully take advantage of column-store characteristics, yet the performance remains outstanding.

<img src="demo-pics/raspi-100.png" style="height: 300px">

In scenarios that fully leverage column-store benefits, the same SQL statement used previously `SELECT con_index, ave_fe1, rmse_ft2, range_fp5 FROM hea_6_c_128;` delivered astonishing results: returning 10 million rows across four columns in just 4 seconds. We believe this is because the Raspberry Pi has fewer cores, which reduces data contention, and the workload perfectly matches the CPU’s most efficient operating range.

<img src="demo-pics/raspi-column.png" style="height: 400px">

## Data Computation Process

The code for the data computation process is located in the `calc_descriptors` directory. The computation process works by having a script submit tasks to a Redis queue, which are then picked up and processed by multiple worker processes.

The core computation process is orchestrated by Python, with certain performance-critical parts implemented in Rust and exposed as Python modules via PyO3. All worker processes involved in the computation run inside Docker containers, with no use of multithreading. Each Docker container utilizes only a single CPU core. This design makes modifying the computation tasks extremely straightforward, as it completely avoids issues related to multithreading or multiprocessing.

The computation process requires:
- One task-submission container
- One or more Redis containers
- Multiple computation worker containers

All computation containers are identical, so they can be easily scaled using `docker-compose --scale`.

The computation program also includes proper signal handling for interruptions: if the program receives an interrupt signal, it will finish the current task before stopping the container gracefully.

As long as the Redis container exposes its port, the computation tasks do not need to run within the same cluster/network. This architecture also supports dynamic scaling (adding or removing workers) at runtime.

## Additional Information

- The real data for this project is stored using object storage compatible with the S3 protocol. The metadata functions similarly to a data directory, enabling multiple users to access the data simultaneously.

- The content in `init.sql` consists of the lakehouse access information, such as `s3_endpoint='idmlakehouse.tmslab.cn';` etc. If you do not start DuckDB using `duckdb --init init.sql`, you can directly input the contents of the `init.sql` file in the DuckDB CLI or use it in Python, which will achieve the same effect.

- Save metadata in SQLite format, and install the corresponding plugin using `install sqlite`, allowing multiple users to access the lakehouse using the same metadata file.

- We have only granted read permissions to the data for general users. Please do not attempt to modify the data. It won't work.

- If you are more accustomed to using Python for data analysis rather than SQL, it is recommended to use Polars instead of Pandas. Taking the JOIN of the two tables in the above image as an example, the lazy loading feature of Polars can save more memory and offers high query efficiency. Pandas, on the other hand, requires caching the entire table in memory, and the original 4GB table consumes approximately 30GB of memory during the query process.

- In our tests, too many CPU cores do not bring performance improvements; instead, they cause serious performance degradation. Too many CPU cores lead to unnecessary data partitioning and transmission. The best full-library query result of 3 minutes 22 seconds was achieved on a 4-core 64G virtual machine. ~~Perhaps using a single core would be faster, but we didn't conduct the corresponding tests.~~

- We've already done the testing — single-core is not faster at all. In the end, the query load on a single core just becomes too heavy. 4–8 cores is the sweet spot for maximum speed. We got incredibly lucky: we landed on the absolute fastest configuration right from the very first try. One more thing I'd like to add: if the data were stored on a flash array and queried with an ultra-high-clock CPU (like on a top-spec Mac), the time would definitely drop well below the current 3:22 record!

- We have also prepared an `init-standalone.sql` file under the `descriptors` path, which allows connecting to the lakehouse without requiring local metadata. We have placed the metadata in OSS as well, and this file directly accesses the metadata file via its URL. This access method requires less than 10 seconds for loading on the first use; thanks to the caching mechanism, subsequent accesses are as fast as the local metadata file solution. This approach effectively resolves matching issues caused by metadata updates, as every rebuilt connection will load the latest metadata file.

- We also tested the approach of using Postgres to store metadata. This solution performs well in terms of speed in internal network environments, but is extremely slow in public network environments. We suspect this is due to the inability to cache the data on Postgres locally.

- ~~When running DuckDB on a Raspberry Pi, if you install the CLI using the official website URL, you will encounter an error when connecting to lakehouse. You need to download the linux-arm64 version from the page: https://github.com/duckdb/duckdb/releases.~~

- The operation on the Raspberry Pi device has been successful. Now, the CLI version from DuckDB's official website is working properly, and it can connect to the lakehouse without issues.

- Important: When doing `que_push.py`, if you're using Docker, **absolutely do NOT** write `restart: always` or `restart: unless-stopped` in your `docker-compose.yml`. Otherwise, after all tasks are finished, the container will automatically restart and begin a second round of computation. Both my colleague and I fell into this exact pitfall the first time we ran the job 😂.

- Tried using [OpenClaw](https://openclaw.ai) to query the database, handed the project link to the Agent, and was able to successfully retrieve the data. Very convenient

  <img src="demo-pics/try_openclaw.png" style="height: 300px">

## License

<a rel="license" href="https://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a>
