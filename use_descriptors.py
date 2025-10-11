"""
This is a simple example of how to use the ducklake connector.
"""

import duckdb

conn: duckdb.DuckDBPyConnection = duckdb.connect()

# Install ducklake
conn.execute("INSTALL ducklake;") # If you have already installed ducklake, you can skip this step.

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
# Print the names of all tables
print("The names of all tables:")
print(conn.sql("SHOW TABLES;"))


# This part is from the remote data (lakehouse)
# Query some real data
print("The first 10 rows of the data:")
print(conn.sql("SELECT con_index, ave_fe1, rmse_ft2, hmix_data FROM hea_6_c_68 limit 10;"))


# Query and display alloy components that meet specific property criteria
print("Alloy components with desired properties:")

elements: tuple[str, ...] = conn.query("""
                                       SELECT elem1, elem2, elem3, elem4, elem5, elem6
                                       FROM hea_elements_6
                                       """).fetchone()
print(f"6 elements of the HEA are {elements[0]}, {elements[1]}, {elements[2]}, {elements[3]}, {elements[4]}, {elements[5]}")

print(conn.sql("""
SELECT hea_6_c_192.con_index, hea_con_6.con1, hea_con_6.con2, hea_con_6.con3, hea_con_6.con4, hea_con_6.con5, hea_con_6.con6
FROM hea_6_c_192
LEFT JOIN hea_con_6 ON hea_6_c_192.con_index = hea_con_6.id
WHERE ave_fe1 > 1.68
AND pair_fe5 > 7.80
AND gg0_data > 0.87
AND tbtm_data > 1732
AND rmse_hmix_data < 0.39;
"""))