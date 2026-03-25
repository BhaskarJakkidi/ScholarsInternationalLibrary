import psycopg2

conn = psycopg2.connect(user='postgres', dbname='postgres', host='localhost', port=5432)
cursor = conn.cursor()
cursor.execute("CREATE USER admin WITH PASSWORD 'admin1231';")
cursor.execute("GRANT ALL PRIVILEGES ON DATABASE postgres TO admin;")
cursor.execute("GRANT CREATE ON SCHEMA public TO admin;")
conn.commit()
conn.close()
print('Admin user created')