from app.services.dataset_manager import get_dataset_manager
import os

dm = get_dataset_manager()

# Check HR dataset
hr_dataset = dm.get_dataset("hr_data")
print(f"\n=== HR Dataset ===")
print(f"Name: {hr_dataset.name}")
print(f"Data Dict Path: {hr_dataset.data_dictionary_path}")
print(f"File exists: {os.path.exists(hr_dataset.data_dictionary_path)}")
print(f"KPI Doc Path: {hr_dataset.kpi_documentation_path}")
print(f"File exists: {os.path.exists(hr_dataset.kpi_documentation_path)}")

# Check Sales dataset
sales_dataset = dm.get_dataset("sales_data")
print(f"\n=== Sales Dataset ===")
print(f"Name: {sales_dataset.name}")
print(f"Data Dict Path: {sales_dataset.data_dictionary_path}")
print(f"File exists: {os.path.exists(sales_dataset.data_dictionary_path)}")
print(f"KPI Doc Path: {sales_dataset.kpi_documentation_path}")
print(f"File exists: {os.path.exists(sales_dataset.kpi_documentation_path)}")

# Check current dataset
print(f"\n=== Current Dataset ===")
print(f"Current ID: {dm.current_dataset_id}")
current = dm.get_current_dataset()
print(f"Current Name: {current.name}")
