#!/usr/bin/env python3
"""
Create a DuckDB metadata catalog for the Parquet file stored in MinIO.

The catalog is a small DuckDB database file (`metadata.duckdb`) that records
where the actual data lives (S3/MinIO). Users can download only this tiny
metadata file and query the full dataset through DuckDB without transferring
the Parquet file itself.
"""

import os

import duckdb

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = os.getenv("MINIO_BUCKET", "hea-minimal")
OBJECT_NAME = os.getenv("MINIO_OBJECT", "results.parquet")
METADATA_PATH = os.getenv("METADATA_PATH", "metadata.duckdb")


def _ensure_httpfs(con: duckdb.DuckDBPyConnection) -> None:
    """Make sure the DuckDB httpfs extension is available."""
    installed = con.execute(
        "SELECT installed FROM duckdb_extensions() WHERE extension_name = 'httpfs'"
    ).fetchone()
    if not installed or not installed[0]:
        con.execute("INSTALL httpfs;")
    con.execute("LOAD httpfs;")


def main() -> None:
    con = duckdb.connect(METADATA_PATH)
    _ensure_httpfs(con)

    # Configure DuckDB to talk to the local MinIO instance.
    con.execute(f"SET s3_endpoint='{MINIO_ENDPOINT}'")
    con.execute(f"SET s3_region='{MINIO_REGION}'")
    con.execute("SET s3_use_ssl=false")
    con.execute("SET s3_url_style='path'")
    con.execute(f"SET s3_access_key_id='{MINIO_ACCESS_KEY}'")
    con.execute(f"SET s3_secret_access_key='{MINIO_SECRET_KEY}'")

    s3_path = f"s3://{BUCKET_NAME}/{OBJECT_NAME}"
    con.execute(f"CREATE OR REPLACE VIEW results AS SELECT * FROM read_parquet('{s3_path}')")

    # Persist the view and S3 settings in the catalog file.
    con.execute("CHECKPOINT")
    con.close()

    print(f"Metadata catalog created: {METADATA_PATH}")
    print(f"It points to: {s3_path}")


if __name__ == "__main__":
    main()
