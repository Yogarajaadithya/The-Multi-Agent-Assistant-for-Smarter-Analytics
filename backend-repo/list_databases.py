"""
Quick script to list all databases in your PostgreSQL instance
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'postgres',  # Connect to default postgres database
    'user': 'postgres',
    'password': 'A1b2c3d4'
}

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # List all databases
    cursor.execute("SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;")
    databases = cursor.fetchall()
    
    print("=" * 60)
    print("Available Databases in PostgreSQL 18 (local):")
    print("=" * 60)
    for idx, (db_name,) in enumerate(databases, 1):
        print(f"{idx}. {db_name}")
    print("=" * 60)
    print(f"\nTotal databases found: {len(databases)}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Error connecting to PostgreSQL: {e}")
