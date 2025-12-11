"""
Setup Multiple Dataset Schemas in PostgreSQL
=============================================
This script creates schemas for different datasets:
- hr_data (already exists)
- sales_data (new)
- customer_data (new - for future use)

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

# Define your datasets
DATASETS = {
    'hr_data': {
        'description': 'HR Employee Attrition Dataset',
        'main_table': 'employee_attrition',
        'already_exists': True
    },
    'sales_data': {
        'description': 'Sales Transactions Dataset',
        'main_table': 'sales_transactions',
        'already_exists': False
    },
    'customer_data': {
        'description': 'Customer Analytics Dataset',
        'main_table': 'customers',
        'already_exists': False
    }
}

print("=" * 80)
print("MULTI-DATASET SCHEMA SETUP")
print("=" * 80)

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = True
    cursor = conn.cursor()
    
    print("\n📁 Creating schemas for multiple datasets...\n")
    
    for schema_name, info in DATASETS.items():
        # Check if schema exists
        cursor.execute(
            f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema_name}';"
        )
        exists = cursor.fetchone()
        
        if exists:
            print(f"  ✓ Schema '{schema_name}' already exists")
            print(f"    Description: {info['description']}")
        else:
            # Create schema
            cursor.execute(f"CREATE SCHEMA {schema_name};")
            print(f"  ✓ Schema '{schema_name}' created successfully")
            print(f"    Description: {info['description']}")
        
        # Create metadata table in each schema (stores dataset info)
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}.dataset_metadata (
                key VARCHAR(255) PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Insert/update metadata
        cursor.execute(f"""
            INSERT INTO {schema_name}.dataset_metadata (key, value)
            VALUES 
                ('dataset_name', '{schema_name}'),
                ('description', '{info['description']}'),
                ('main_table', '{info['main_table']}'),
                ('created_date', CURRENT_TIMESTAMP::TEXT)
            ON CONFLICT (key) 
            DO UPDATE SET value = EXCLUDED.value, updated_at = CURRENT_TIMESTAMP;
        """)
        
        print(f"    └── Metadata table created/updated")
        print()
    
    cursor.close()
    conn.close()
    
    print("=" * 80)
    print("✓ All schemas created successfully!")
    print("=" * 80)
    
    print("\n📊 Dataset Structure:")
    print("""
    PostgreSQL Database: postgres
    ├── Schema: hr_data
    │   ├── employee_attrition (1,470 rows) ✓
    │   └── dataset_metadata
    ├── Schema: sales_data
    │   ├── sales_transactions (ready for data)
    │   └── dataset_metadata
    └── Schema: customer_data
        ├── customers (ready for data)
        └── dataset_metadata
    """)
    
    print("\n🎯 Next Steps:")
    print("1. Upload sales data using: upload_sales_data.py")
    print("2. Upload customer data using: upload_customer_data.py")
    print("3. Update backend to support dataset switching")
    
except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
