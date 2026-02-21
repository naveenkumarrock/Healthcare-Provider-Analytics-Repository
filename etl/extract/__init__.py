"""
Extraction Layer
Handles data ingestion from:
    - MySQL
    - CSV files
    - APIs (future)
"""

from .extract import extract_from_mysql
# If you have CSV extraction:
# from .extract import extract_from_csv

__all__ = [
    "extract_from_mysql",
    # "extract_from_csv",
]