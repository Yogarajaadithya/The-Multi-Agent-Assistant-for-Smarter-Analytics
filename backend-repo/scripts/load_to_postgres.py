"""
PostgreSQL Data Loader Script
------------------------------
Automatically uploads local data files (CSV, Excel, Parquet) to PostgreSQL database.

Usage:
    python load_to_postgres.py --file "path/to/data.csv" --table table_name --if-exists replace
    python load_to_postgres.py --file "path/to/data.xlsx" --table table_name --if-exists append
    python load_to_postgres.py --file "path/to/data.parquet" --table table_name

Arguments:
    --file: Path to the data file (CSV, Excel, or Parquet)
    --table: Target table name in PostgreSQL
    --if-exists: How to behave if table exists ('replace', 'append', 'fail'). Default: 'replace'
    --chunksize: Number of rows to insert at once. Default: 10000
"""

import argparse
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import time

# Check for optional parquet support
try:
    import pyarrow.parquet as pq
    PARQUET_SUPPORT = True
except ImportError:
    PARQUET_SUPPORT = False


# PostgreSQL connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'postgres',  # Default database, change to 'myprojectdb' if you created it
    'user': 'postgres',
    'password': 'A1b2c3d4'
}


def create_db_connection():
    """
    Create and return a SQLAlchemy database engine.
    
    Returns:
        sqlalchemy.engine.Engine: Database connection engine
    """
    connection_string = (
        f"postgresql+psycopg2://{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    )
    
    try:
        engine = create_engine(connection_string, echo=False)
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"✓ Successfully connected to PostgreSQL database: {DB_CONFIG['database']}")
        return engine
    except SQLAlchemyError as e:
        print(f"✗ Failed to connect to PostgreSQL database.")
        print(f"Error: {e}")
        sys.exit(1)


def load_data_file(file_path):
    """
    Load data from CSV, Excel, or Parquet file into a pandas DataFrame.
    
    Args:
        file_path (str): Path to the data file
        
    Returns:
        pd.DataFrame: Loaded data
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"✗ File not found: {file_path}")
        sys.exit(1)
    
    file_extension = file_path.suffix.lower()
    
    print(f"\n📂 Loading file: {file_path.name}")
    print(f"   Format: {file_extension}")
    
    try:
        start_time = time.time()
        
        if file_extension == '.csv':
            df = pd.read_csv(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
        elif file_extension == '.parquet':
            if not PARQUET_SUPPORT:
                print(f"✗ Parquet support not available!")
                print("   Install pyarrow to read Parquet files: pip install pyarrow")
                sys.exit(1)
            df = pd.read_parquet(file_path)
        else:
            print(f"✗ Unsupported file format: {file_extension}")
            supported_formats = ".csv, .xlsx, .xls"
            if PARQUET_SUPPORT:
                supported_formats += ", .parquet"
            print(f"   Supported formats: {supported_formats}")
            sys.exit(1)
        
        load_time = time.time() - start_time
        
        print(f"✓ File loaded successfully in {load_time:.2f} seconds")
        print(f"   Rows: {len(df):,}")
        print(f"   Columns: {len(df.columns)}")
        print(f"   Column names: {', '.join(df.columns.tolist())}")
        
        # Display data types
        print(f"\n📊 Data Types:")
        for col, dtype in df.dtypes.items():
            print(f"   - {col}: {dtype}")
        
        return df
        
    except Exception as e:
        print(f"✗ Failed to load file: {e}")
        sys.exit(1)


def upload_to_postgres(df, table_name, engine, if_exists='replace', chunksize=10000):
    """
    Upload DataFrame to PostgreSQL database.
    
    Args:
        df (pd.DataFrame): Data to upload
        table_name (str): Target table name
        engine (sqlalchemy.engine.Engine): Database connection engine
        if_exists (str): How to behave if table exists ('replace', 'append', 'fail')
        chunksize (int): Number of rows to insert at once
    """
    print(f"\n🚀 Starting upload to table: {table_name}")
    print(f"   Mode: {if_exists}")
    print(f"   Chunk size: {chunksize:,} rows")
    
    total_rows = len(df)
    
    try:
        start_time = time.time()
        
        # Upload data in chunks with progress tracking
        if total_rows <= chunksize:
            # Small dataset - upload in one go
            df.to_sql(
                name=table_name,
                con=engine,
                if_exists=if_exists,
                index=False,
                method='multi'
            )
            print(f"   Progress: {total_rows:,}/{total_rows:,} rows (100%)")
        else:
            # Large dataset - upload in chunks
            for i, chunk_start in enumerate(range(0, total_rows, chunksize)):
                chunk_end = min(chunk_start + chunksize, total_rows)
                chunk = df.iloc[chunk_start:chunk_end]
                
                # First chunk: use if_exists parameter
                # Subsequent chunks: always append
                mode = if_exists if i == 0 else 'append'
                
                chunk.to_sql(
                    name=table_name,
                    con=engine,
                    if_exists=mode,
                    index=False,
                    method='multi'
                )
                
                progress = (chunk_end / total_rows) * 100
                print(f"   Progress: {chunk_end:,}/{total_rows:,} rows ({progress:.1f}%)")
        
        upload_time = time.time() - start_time
        rows_per_second = total_rows / upload_time if upload_time > 0 else 0
        
        print(f"\n✓ Upload completed successfully!")
        print(f"   Total time: {upload_time:.2f} seconds")
        print(f"   Speed: {rows_per_second:,.0f} rows/second")
        
    except SQLAlchemyError as e:
        print(f"\n✗ Upload failed!")
        print(f"Error: {e}")
        sys.exit(1)


def verify_upload(table_name, engine):
    """
    Verify the upload by querying the row count and showing sample data.
    
    Args:
        table_name (str): Table name to verify
        engine (sqlalchemy.engine.Engine): Database connection engine
    """
    print(f"\n🔍 Verifying upload...")
    
    try:
        with engine.connect() as conn:
            # Get row count
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            row_count = result.scalar()
            
            print(f"✓ Table '{table_name}' now contains {row_count:,} rows")
            
            # Show sample data (first 5 rows)
            sample_df = pd.read_sql(f"SELECT * FROM {table_name} LIMIT 5", conn)
            
            if not sample_df.empty:
                print(f"\n📋 Sample data (first 5 rows):")
                print(sample_df.to_string(index=False))
            
    except SQLAlchemyError as e:
        print(f"✗ Verification failed: {e}")


def main():
    """Main function to parse arguments and execute the upload."""
    parser = argparse.ArgumentParser(
        description='Upload local data files to PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python load_to_postgres.py --file data.csv --table customers --if-exists replace
  python load_to_postgres.py --file sales.xlsx --table sales --if-exists append
  python load_to_postgres.py --file events.parquet --table events --chunksize 5000
        """
    )
    
    parser.add_argument(
        '--file',
        required=True,
        help='Path to the data file (CSV, Excel, or Parquet)'
    )
    
    parser.add_argument(
        '--table',
        required=True,
        help='Target table name in PostgreSQL'
    )
    
    parser.add_argument(
        '--if-exists',
        choices=['replace', 'append', 'fail'],
        default='replace',
        help="How to behave if table exists (default: 'replace')"
    )
    
    parser.add_argument(
        '--chunksize',
        type=int,
        default=10000,
        help='Number of rows to insert at once (default: 10000)'
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("PostgreSQL Data Loader")
    print("=" * 70)
    
    # Step 1: Create database connection
    engine = create_db_connection()
    
    # Step 2: Load data file
    df = load_data_file(args.file)
    
    # Step 3: Upload to PostgreSQL
    upload_to_postgres(
        df=df,
        table_name=args.table,
        engine=engine,
        if_exists=args.if_exists,
        chunksize=args.chunksize
    )
    
    # Step 4: Verify upload
    verify_upload(args.table, engine)
    
    print("\n" + "=" * 70)
    print("✓ All operations completed successfully!")
    print("=" * 70)
    
    # Close connection
    engine.dispose()


if __name__ == '__main__':
    main()
