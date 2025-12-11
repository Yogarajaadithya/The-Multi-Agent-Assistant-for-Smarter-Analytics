"""
Upload Sales Data to PostgreSQL
================================
Upload your sales dataset to the sales_data schema

Author: Yogarajaadithya
Date: December 10, 2025
"""
import psycopg2
from sqlalchemy import create_engine
import pandas as pd
import os

# Local PostgreSQL Configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'A1b2c3d4'
}

SCHEMA_NAME = 'sales_data'
TABLE_NAME = 'zalando_sales'

# Path to Zalando sales dataset
CSV_FILE_PATH = r"D:\Capstone_Prj\prod\The-Multi-Agent-Assistant-for-Smarter-Analytics\The-Multi-Agent-Assistant-for-Smarter-Analytics\data\sales_data\zalando_dummy_dataset.csv"

print("=" * 80)
print(f"UPLOADING SALES DATA TO '{SCHEMA_NAME}' SCHEMA")
print("=" * 80)

# Check if file exists
if not os.path.exists(CSV_FILE_PATH):
    print(f"\n⚠️  CSV file not found: {CSV_FILE_PATH}")
    print("\n📝 Please update the CSV_FILE_PATH variable with your sales data file location")
    print("\nExample:")
    print('  CSV_FILE_PATH = r"D:\\data\\my_sales_data.csv"')
    exit(1)

# Load CSV file
print(f"\n📂 Loading file: {CSV_FILE_PATH}")
try:
    df = pd.read_csv(CSV_FILE_PATH)
    print(f"✓ File loaded successfully")
    print(f"   Rows: {len(df):,}")
    print(f"   Columns: {len(df.columns)}")
    print(f"\n📋 Column names:")
    for i, col in enumerate(df.columns, 1):
        print(f"   {i:2d}. {col}")
except Exception as e:
    print(f"✗ Error loading file: {e}")
    exit(1)

# Upload to PostgreSQL
print(f"\n🚀 Uploading to schema '{SCHEMA_NAME}', table '{TABLE_NAME}'...")

try:
    connection_string = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    engine = create_engine(connection_string)
    
    df.to_sql(
        name=TABLE_NAME,
        con=engine,
        schema=SCHEMA_NAME,
        if_exists='replace',  # Use 'append' to add to existing data
        index=False,
        method='multi'
    )
    
    print(f"✓ Upload completed successfully!")
    
    # Verify
    result = pd.read_sql(f"SELECT COUNT(*) as count FROM {SCHEMA_NAME}.{TABLE_NAME}", engine)
    row_count = result['count'][0]
    print(f"\n🔍 Verification:")
    print(f"✓ Table '{SCHEMA_NAME}.{TABLE_NAME}' contains {row_count:,} rows")
    
    # Show sample
    sample = pd.read_sql(f"SELECT * FROM {SCHEMA_NAME}.{TABLE_NAME} LIMIT 3", engine)
    print(f"\n📊 Sample data (first 3 rows):")
    print(sample.to_string(index=False))
    
    engine.dispose()
    
except Exception as e:
    print(f"✗ Error uploading data: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n" + "=" * 80)
print("✓ Sales data upload completed successfully!")
print(f"✓ Access your data: SELECT * FROM {SCHEMA_NAME}.{TABLE_NAME};")
print("=" * 80)
