import psycopg2

# Connection details from Aiven console
conn = psycopg2.connect(
    host="",
    port="",
    dbname="",
    user="",
    password="",
    sslmode=""
)

cur = conn.cursor()

# Read and execute the SQL file
with open("scripts/init-db.sql", "r") as f:
    sql = f.read()
    cur.execute(sql)

conn.commit()
cur.close()
conn.close()
