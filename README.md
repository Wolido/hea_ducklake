<img src="https://disc-wolido.oss-cn-beijing.aliyuncs.com/idm-logo/%E6%B5%85%E8%89%B2%E8%83%8C%E6%99%AFlogo-%E5%B7%A6%E5%8F%B3.png" style="height: 60px" />

# HEA DuckLake

This project includes a foundational database for six principal elements high-entropy alloys, suitable for computations, ML training and predictions based on high-entropy alloys.

The data is distributed in the form of DuckLake's lakehouse. The project contains DuckLake's metadata files as well as an `init.sql` file for accessing the data lakehouse.

The actual total data volume of the project is nearly 20TB. Thanks to DuckLake's lakehouse technology, you only need to download tens of megabytes of metadata to remotely access the entire database.

There are two accessible data lakehouses in the project: one is the descriptors for high-entropy alloys under the `descriptor` path, and the other is a set of ML model prediction results under the pred_demo path. Files ending with `.ducklake` are metadata files for the lakehouse.

The descriptor lakehouse contains a table of element combinations named `hea_elements_6`; a table of element composition ratios named `hea_con_6`; and an explanation table for descriptor field names named `descriptor_names`. These tables can help you better understand and use the lakehouse when querying the descriptor tables. The naming format for the descriptor data tables is `hea_6_c_x`, where `x` is the index of the element combination in the `hea_elements_6` table.

The naming format for the tables in the prediction data lakehouse is `pred_x`, where `x` is the index of the element combination in the `hea_elements_6` table of the descriptor lakehouse.

## Usage: Taking the metadata under the descriptors path as an example

### Through DuckDB

- Install DuckDB Command Line Client: Visit the following website to install the CLI program https://duckdb.org/install/?platform=macos&environment=cli

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

## Additional Information

- The real data for this project is stored using OSS compatible with the S3 protocol. The metadata functions similarly to a data directory, enabling multiple users to access the data simultaneously.

- The content in `init.sql` consists of the lakehouse access information, such as `s3_endpoint='idmlakehouse.tmslab.cn';` etc. If you do not start DuckDB using `duckdb --init init.sql`, you can directly input the contents of the `init.sql` file in the DuckDB CLI or use it in Python, which will achieve the same effect.

- We have only granted read permissions to the data for general users. Please do not attempt to modify the data. It won't work.

- If you are more accustomed to using Python for data analysis rather than SQL, it is recommended to use Polars instead of Pandas. Taking the JOIN of the two tables in the above image as an example, the lazy loading feature of Polars can save more memory and offers high query efficiency. Pandas, on the other hand, requires caching the entire table in memory, and the original 4GB table consumes approximately 30GB of memory during the query process.

## License

<a rel="license" href="https://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/88x31.png" /></a>
