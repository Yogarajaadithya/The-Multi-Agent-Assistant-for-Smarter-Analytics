"""
Dataset Manager Service
=======================
Manages multiple datasets and handles dynamic switching between them.

Author: Yogarajaadithya
Date: December 10, 2025
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import os
from pathlib import Path


@dataclass
class DatasetInfo:
    """Information about a dataset"""
    id: str
    name: str
    description: str
    schema_name: str
    main_table: str
    data_dictionary_path: str
    kpi_documentation_path: str
    row_count: Optional[int] = None
    

class DatasetManager:
    """Manages multiple datasets and switching between them"""
    
    def __init__(self):
        self.datasets: Dict[str, DatasetInfo] = {}
        self.current_dataset_id: str = os.getenv("DEFAULT_DATASET", "hr_data")
        self._initialize_datasets()
    
    def _initialize_datasets(self):
        """Initialize available datasets"""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        
        # HR Dataset
        self.datasets["hr_data"] = DatasetInfo(
            id="hr_data",
            name="HR Employee Attrition",
            description="Employee attrition and HR analytics dataset",
            schema_name="hr_data",
            main_table="employee_attrition",
            data_dictionary_path=str(project_root / "data" / "hr_data" / "HR_Data_Dictionary.csv"),
            kpi_documentation_path=str(project_root / "data" / "hr_data" / "hr_kpi_documentation.txt")
        )
        
        # Sales Dataset (Zalando)
        self.datasets["sales_data"] = DatasetInfo(
            id="sales_data",
            name="Zalando Sales",
            description="E-commerce sales transactions and customer analytics",
            schema_name="sales_data",
            main_table="zalando_sales",
            data_dictionary_path=str(project_root / "data" / "sales_data" / "zalando_data_dictionary.csv"),
            kpi_documentation_path=str(project_root / "data" / "sales_data" / "zalando_kpi_documentation.txt")
        )
    
    def get_all_datasets(self) -> List[Dict]:
        """Get list of all available datasets"""
        return [
            {
                "id": ds.id,
                "name": ds.name,
                "description": ds.description,
                "schema_name": ds.schema_name,
                "main_table": ds.main_table,
                "is_active": ds.id == self.current_dataset_id
            }
            for ds in self.datasets.values()
        ]
    
    def get_dataset(self, dataset_id: str) -> Optional[DatasetInfo]:
        """Get information about a specific dataset"""
        return self.datasets.get(dataset_id)
    
    def get_current_dataset(self) -> DatasetInfo:
        """Get the currently active dataset"""
        return self.datasets[self.current_dataset_id]
    
    def switch_dataset(self, dataset_id: str) -> bool:
        """
        Switch to a different dataset
        
        Args:
            dataset_id: The ID of the dataset to switch to
            
        Returns:
            bool: True if successful, False otherwise
        """
        if dataset_id not in self.datasets:
            return False
        
        self.current_dataset_id = dataset_id
        return True
    
    def get_schema_name(self) -> str:
        """Get the schema name for the current dataset"""
        return self.get_current_dataset().schema_name
    
    def get_table_name(self) -> str:
        """Get the main table name for the current dataset"""
        return self.get_current_dataset().main_table
    
    def get_data_dictionary_path(self) -> str:
        """Get the data dictionary path for the current dataset"""
        return self.get_current_dataset().data_dictionary_path
    
    def get_kpi_documentation_path(self) -> str:
        """Get the KPI documentation path for the current dataset"""
        return self.get_current_dataset().kpi_documentation_path


# Global dataset manager instance
_dataset_manager: Optional[DatasetManager] = None


def get_dataset_manager() -> DatasetManager:
    """Get or create the global dataset manager instance"""
    global _dataset_manager
    if _dataset_manager is None:
        _dataset_manager = DatasetManager()
    return _dataset_manager
