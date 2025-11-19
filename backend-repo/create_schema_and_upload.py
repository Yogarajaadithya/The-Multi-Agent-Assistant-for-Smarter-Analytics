"""
Create schema and upload data to PostgreSQL with schema support
"""
import psycopg2
from sqlalchemy import create_engine
import pandas as pd

DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'A1b2c3d4'
}

schema_name = 'hr_data'

print("=" * 70)
print("Creating Schema and Uploading Data")
print("=" * 70)

# Step 1: Create schema
try:
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if schema exists
    cursor.execute(f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}';")
    exists = cursor.fetchone()
    
    if exists:
        print(f"✓ Schema '{schema_name}' already exists")
    else:
        cursor.execute(f"CREATE SCHEMA {schema_name};")
        print(f"✓ Schema '{schema_name}' created successfully")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"✗ Error creating schema: {e}")
    exit(1)

# Step 2: Load data
print(f"\n📂 Loading file: hr_employee_attrition.csv")
file_path = r"D:\Capstone_Prj\The-Multi-Agent-Assistant-for-Smarter-Analytics\hr_employee_attrition.csv"

try:
    df = pd.read_csv(file_path)
    print(f"✓ File loaded successfully")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
except Exception as e:
    print(f"✗ Error loading file: {e}")
    exit(1)

# Step 3: Upload to schema
print(f"\n🚀 Uploading to schema '{schema_name}', table 'employee_attrition'")

try:
    connection_string = f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    engine = create_engine(connection_string)
    
    df.to_sql(
        name='employee_attrition',
        con=engine,
        schema=schema_name,
        if_exists='replace',
        index=False,
        method='multi'
    )
    
    print(f"✓ Upload completed successfully!")
    
    # Verify
    result = pd.read_sql(f"SELECT COUNT(*) as count FROM {schema_name}.employee_attrition", engine)
    row_count = result['count'][0]
    print(f"\n🔍 Verification:")
    print(f"✓ Table '{schema_name}.employee_attrition' contains {row_count:,} rows")
    
    # Show sample
    sample = pd.read_sql(f"SELECT * FROM {schema_name}.employee_attrition LIMIT 3", engine)
    print(f"\n📋 Sample data (first 3 rows):")
    print(sample.to_string(index=False))
    
    engine.dispose()
    
except Exception as e:
    print(f"✗ Error uploading data: {e}")
    exit(1)

print("\n" + "=" * 70)
print("✓ All operations completed successfully!")
print(f"✓ Access your data: SELECT * FROM {schema_name}.employee_attrition;")
print("=" * 70)
