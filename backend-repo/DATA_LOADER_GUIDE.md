# PostgreSQL Data Loader Guide

## Overview
This script automatically uploads local data files (CSV, Excel, or Parquet) to your PostgreSQL database running on `localhost:5433`.

## Prerequisites
- PostgreSQL 18 is installed and running on port 5433
- Database `myprojectdb` exists
- User `postgres` with password `A1b2c3d4` has write access

## Installation
```powershell
# Activate virtual environment and install dependencies
cd backend-repo
.\venv-py311\Scripts\Activate.ps1
pip install -r requirements-data.txt
```

## Usage

### Basic Usage
```powershell
# Load CSV file (replace existing table)
python load_to_postgres.py --file "C:/path/to/data.csv" --table customers

# Load Excel file (append to existing table)
python load_to_postgres.py --file "C:/path/to/sales.xlsx" --table sales --if-exists append

# Load with custom chunk size for large files
python load_to_postgres.py --file "C:/path/to/large_data.csv" --table events --chunksize 5000
```

### Command Line Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--file` | Yes | - | Path to the data file (CSV, Excel, or Parquet) |
| `--table` | Yes | - | Target table name in PostgreSQL |
| `--if-exists` | No | `replace` | How to behave if table exists: `replace`, `append`, or `fail` |
| `--chunksize` | No | `10000` | Number of rows to insert at once |

### Examples

#### Example 1: Upload Customer Data (CSV)
```powershell
python load_to_postgres.py --file "D:/data/customers.csv" --table customers --if-exists replace
```

**Output:**
```
======================================================================
PostgreSQL Data Loader
======================================================================
✓ Successfully connected to PostgreSQL database: myprojectdb

📂 Loading file: customers.csv
   Format: .csv
✓ File loaded successfully in 0.45 seconds
   Rows: 10,000
   Columns: 5
   Column names: id, name, email, age, city

📊 Data Types:
   - id: int64
   - name: object
   - email: object
   - age: int64
   - city: object

🚀 Starting upload to table: customers
   Mode: replace
   Chunk size: 10,000 rows
   Progress: 10,000/10,000 rows (100%)

✓ Upload completed successfully!
   Total time: 1.23 seconds
   Speed: 8,130 rows/second

🔍 Verifying upload...
✓ Table 'customers' now contains 10,000 rows

📋 Sample data (first 5 rows):
   id      name              email  age       city
    1  John Doe   john@email.com   35  New York
    2  Jane Smith jane@email.com   28    Boston
  ...

======================================================================
✓ All operations completed successfully!
======================================================================
```

#### Example 2: Append Sales Data (Excel)
```powershell
python load_to_postgres.py --file "D:/data/monthly_sales.xlsx" --table sales --if-exists append
```

#### Example 3: Large File with Custom Chunk Size
```powershell
python load_to_postgres.py --file "D:/data/big_dataset.csv" --table analytics --chunksize 5000
```

## Features

✅ **Automatic Table Creation** - Tables are created automatically with inferred schema from your data

✅ **Multiple File Formats** - Supports CSV, Excel (.xlsx, .xls), and Parquet (if pyarrow is installed)

✅ **Chunked Uploads** - Efficiently handles large files by uploading in chunks

✅ **Progress Tracking** - Real-time progress updates during upload

✅ **Data Validation** - Verifies successful insertion with row count confirmation

✅ **Flexible Modes** - Choose to replace, append, or fail if table exists

## Configuration

To modify database connection parameters, edit the `DB_CONFIG` dictionary in `load_to_postgres.py`:

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5433,
    'database': 'myprojectdb',
    'user': 'postgres',
    'password': 'A1b2c3d4'
}
```

## Troubleshooting

### Connection Failed
**Error:** `Failed to connect to PostgreSQL database`

**Solution:**
1. Ensure PostgreSQL is running: Open pgAdmin or DBeaver
2. Verify port 5433 is correct
3. Check username and password in the script
4. Confirm database `myprojectdb` exists

### File Not Found
**Error:** `File not found: /path/to/file.csv`

**Solution:**
- Use absolute paths (e.g., `C:/Users/username/data/file.csv`)
- On Windows, use forward slashes (/) or escape backslashes (\\\\)

### Unsupported File Format
**Error:** `Unsupported file format: .parquet`

**Solution:**
- For Parquet support, install pyarrow: `pip install pyarrow`
- Note: pyarrow requires C++ build tools on Windows

### Table Already Exists
**Error:** `Table 'tablename' already exists`

**Solution:**
- Use `--if-exists replace` to overwrite the table
- Use `--if-exists append` to add data to existing table
- Use `--if-exists fail` to raise an error (default behavior if not specified as 'replace')

## Advanced Usage

### Using in a Python Script
```python
from load_to_postgres import create_db_connection, load_data_file, upload_to_postgres

# Create connection
engine = create_db_connection()

# Load data
df = load_data_file("path/to/data.csv")

# Upload to PostgreSQL
upload_to_postgres(df, "my_table", engine, if_exists='replace', chunksize=10000)
```

### Query Data After Upload
```python
import pandas as pd
from sqlalchemy import create_engine

# Connect
engine = create_engine("postgresql+psycopg2://postgres:A1b2c3d4@localhost:5433/myprojectdb")

# Query data
df = pd.read_sql("SELECT * FROM customers LIMIT 10", engine)
print(df)
```

## Tips

- **Large Files:** Increase `--chunksize` for faster uploads (try 50000 for files with millions of rows)
- **Data Types:** pandas automatically infers data types, but you can manually cast before upload if needed
- **Performance:** For best performance, ensure PostgreSQL has adequate memory settings
- **Backups:** Always backup existing tables before using `--if-exists replace`

## Support

For issues or questions:
1. Check PostgreSQL connection using DBeaver
2. Verify file path and format
3. Review error messages for specific issues
4. Ensure all dependencies are installed: `pip list`
