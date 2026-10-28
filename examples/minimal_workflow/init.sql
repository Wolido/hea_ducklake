-- DuckDB initialization for the minimal workflow lakehouse.
-- Attach to the metadata catalog and configure S3 access to the local MinIO instance.

ATTACH 'metadata.duckdb' AS hea_minimal;
USE hea_minimal;

SET s3_endpoint='localhost:9000';
SET s3_use_ssl=false;
SET s3_url_style='path';
SET s3_access_key_id='minioadmin';
SET s3_secret_access_key='minioadmin';
