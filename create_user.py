import psycopg2

import db_utils

DB_CONFIG = db_utils.get_db_config();
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()
cursor.execute("CREATE USER admin WITH PASSWORD 'admin1231';")
cursor.execute("GRANT ALL PRIVILEGES ON DATABASE postgres TO admin;")
cursor.execute("GRANT CREATE ON SCHEMA public TO admin;")
conn.commit()
conn.close()
print('Admin user created')