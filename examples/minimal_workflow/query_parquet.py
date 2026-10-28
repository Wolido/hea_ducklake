#!/usr/bin/env python3
"""
Query the Parquet result with DuckDB.

This demonstrates the data-access side of the hea_ducklake framework: users
can run SQL directly on columnar Parquet files without importing the data
into a heavyweight database server.
"""

import os

import duckdb

INPUT_PARQUET = os.getenv("OUTPUT_PARQUET", "results.parquet")


def main() -> None:
    if not os.path.exists(INPUT_PARQUET):
        print(f"Input Parquet not found: {INPUT_PARQUET}", file=os.sys.stderr)
        print("Run convert_to_parquet.py first.", file=os.sys.stderr)
        os.sys.exit(1)

    con = duckdb.connect()
    con.execute(f"CREATE VIEW results AS SELECT * FROM read_parquet('{INPUT_PARQUET}')")

    print("Sample query: first 5 rows of con_index and ave_0")
    print(con.execute("SELECT con_index, ave_0 FROM results LIMIT 5").fetchdf())

    print("\nSample aggregation: count and average of ave_0")
    print(con.execute("SELECT COUNT(*), AVG(ave_0) FROM results").fetchdf())


if __name__ == "__main__":
    main()
