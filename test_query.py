import duckdb

# Connect to your DuckDB file
conn = duckdb.connect("library.duckdb")

# Run a query
rows = conn.execute("select * FROM users").fetchall()

for row in rows:
    print(row)

conn.close()