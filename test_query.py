import duckdb
DB_NAME = "mnt/data/library.duckdb"
def connect_db():
    # Persistent DuckDB file
    return duckdb.connect(DB_NAME)
# Connect to your DuckDB file
conn = connect_db()

# Run a query
rows = conn.execute("select *  FROM users").fetchall()

for row in rows:
    print(row)

conn.close()