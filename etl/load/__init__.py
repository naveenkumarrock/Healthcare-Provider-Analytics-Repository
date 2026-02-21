"""
Load Layer
Loads transformed data into:
    - BigQuery
    - Parquet fallback
"""

from .load_to_bigquery import load_to_bigquery

__all__ = [
    "load_to_bigquery",
]