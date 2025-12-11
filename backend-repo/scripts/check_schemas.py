"""
Check existing schemas in local PostgreSQL database
"""
import psycopg2

# Local PostgreSQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'A1b2c3d4'
}

print("=" * 70)
print("Checking Local PostgreSQL Schemas")
print("=" * 70)

try:
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    
    # Get all user schemas (exclude system schemas)
    cursor.execute("""
        SELECT schema_name 
        FROM information_schema.schemata 
        WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
        ORDER BY schema_name;
    """)
    
    schemas = cursor.fetchall()
    
    print(f"\n📂 Found {len(schemas)} user schema(s):\n")
    
    for schema in schemas:
        schema_name = schema[0]
        print(f"  📁 Schema: {schema_name}")
        
        # Get tables in this schema
        cursor.execute(f"""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = '{schema_name}' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        
        if tables:
            for table in tables:
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {schema_name}.{table[0]}")
                count = cursor.fetchone()[0]
                print(f"     └── {table[0]} ({count:,} rows)")
        else:
            print(f"     └── (no tables)")
        print()
    
    cursor.close()
    conn.close()
    
    print("=" * 70)
    print("✓ Schema check completed!")
    print("=" * 70)

except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()
