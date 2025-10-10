"""
This is a simple example of how to use the ducklake connector.
"""

import duckdb

conn: duckdb.DuckDBPyConnection = duckdb.connect()

# Set up the connection
conn.execute("SET s3_endpoint='idmlakehouse.tmslab.cn';")
conn.execute("SET s3_url_style='path';")
conn.execute("SET s3_use_ssl='false';")
conn.execute("""
ATTACH 'ducklake:./descriptors/metadata.ducklake' as hea (
    DATA_PATH 's3://idmdatabase/hea'
);
""")
conn.execute("use hea;")

# This part is from the metadata.ducklake file
print(conn.sql("show tables;"))