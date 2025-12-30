import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='postgres',
    user='postgres',
    password='A1b2c3d4'
)

cur = conn.cursor()
cur.execute("""
    SELECT table_schema, table_name 
    FROM information_schema.tables 
    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ORDER BY table_schema, table_name
""")

print("\n=== Available Tables ===")
for schema, table in cur.fetchall():
    print(f"{schema}.{table}")

conn.close()
