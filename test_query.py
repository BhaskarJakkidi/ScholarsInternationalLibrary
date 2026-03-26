import psycopg2

conn = psycopg2.connect(
    "postgresql://postgres:TpqTueRhigoVZeNksTpfdIWggGWoircA@crossover.proxy.rlwy.net:30362/railway"
)
cursor = conn.cursor()
cursor.execute("SELECT 1;")
print(cursor.fetchone())
conn.close()
