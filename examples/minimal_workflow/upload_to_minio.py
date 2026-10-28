#!/usr/bin/env python3
"""
Upload the Parquet result to the local MinIO instance.

This demonstrates the S3-compatible object-storage layer used by the full
hea_ducklake database. In production the same Parquet files would be stored in
an S3-compatible cloud object store.
"""

import os

from minio import Minio

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_REGION = os.getenv("MINIO_REGION", "us-east-1")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = os.getenv("MINIO_BUCKET", "hea-minimal")
OBJECT_NAME = os.getenv("MINIO_OBJECT", "results.parquet")
INPUT_PARQUET = os.getenv("OUTPUT_PARQUET", "results.parquet")


def main() -> None:
    if not os.path.exists(INPUT_PARQUET):
        print(f"Input Parquet not found: {INPUT_PARQUET}", file=os.sys.stderr)
        print("Run convert_to_parquet.py first.", file=os.sys.stderr)
        os.sys.exit(1)

    client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
        region=MINIO_REGION,
    )

    if not client.bucket_exists(BUCKET_NAME):
        client.make_bucket(BUCKET_NAME)
        print(f"Created bucket: {BUCKET_NAME}")

    client.fput_object(BUCKET_NAME, OBJECT_NAME, INPUT_PARQUET)
    print(f"Uploaded s3://{BUCKET_NAME}/{OBJECT_NAME} from {INPUT_PARQUET}")


if __name__ == "__main__":
    main()
