#!/usr/bin/env python3
"""
Query the dataset through the DuckDB metadata catalog.

This demonstrates the access pattern used by hea_ducklake: a user downloads a
small metadata catalog and queries remote Parquet data via DuckDB SQL without
needing to copy the entire dataset locally.
"""

import os

import duckdb

METADATA_PATH = os.getenv("METADATA_PATH", "metadata.duckdb")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")


def _ensure_httpfs(con: duckdb.DuckDBPyConnection) -> None:
    installed = con.execute(
        "SELECT installed FROM duckdb_extensions() WHERE extension_name = 'httpfs'"
    ).fetchone()
    if not installed or not installed[0]:
        con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")


def _configure_s3(con: duckdb.DuckDBPyConnection) -> None:
    """Configure the httpfs extension to talk to the S3-compatible store."""
    con.execute(f"SET s3_endpoint='{MINIO_ENDPOINT}'")
    con.execute(f"SET s3_region='{MINIO_REGION}'")
    con.execute("SET s3_use_ssl=false")
    con.execute("SET s3_url_style='path'")
    con.execute(f"SET s3_access_key_id='{MINIO_ACCESS_KEY}'")
    con.execute(f"SET s3_secret_access_key='{MINIO_SECRET_KEY}'")


def main() -> None:
    if not os.path.exists(METADATA_PATH):
        print(f"Metadata catalog not found: {METADATA_PATH}", file=os.sys.stderr)
        print("Run create_metadata.py first.", file=os.sys.stderr)
        os.sys.exit(1)

    con = duckdb.connect(METADATA_PATH)
    _ensure_httpfs(con)
    _configure_s3(con)

    print("Sample query through metadata catalog: first 5 rows")
    print(con.execute("SELECT con_index, ave_0 FROM results LIMIT 5").fetchdf())

    print("\nAggregation through metadata catalog")
    print(con.execute("SELECT COUNT(*), AVG(ave_0) FROM results").fetchdf())

    con.close()


if __name__ == "__main__":
    main()
