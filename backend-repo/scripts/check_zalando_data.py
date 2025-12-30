import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5433,
    database='postgres',
    user='postgres',
    password='A1b2c3d4'
)

cur = conn.cursor()

# Check if zalando_sales table has data
cur.execute("SELECT COUNT(*) FROM sales_data.zalando_sales")
count = cur.fetchone()[0]

print(f"\n=== Zalando Sales Data ===")
print(f"Total rows in sales_data.zalando_sales: {count}")

if count > 0:
    cur.execute("SELECT * FROM sales_data.zalando_sales LIMIT 3")
    rows = cur.fetchall()
    cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema='sales_data' AND table_name='zalando_sales'")
    columns = [row[0] for row in cur.fetchall()]
    
    print(f"\nColumns: {', '.join(columns)}")
    print(f"\nSample data (first 3 rows):")
    for row in rows:
        print(row[:5])  # Print first 5 columns

conn.close()
