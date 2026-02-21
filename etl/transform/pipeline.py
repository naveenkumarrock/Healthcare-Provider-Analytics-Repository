"""
ETL Pipeline Orchestrator: Extract → Transform → Load
Runs the full pipeline from source data to BigQuery (or Parquet fallback).
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from etl.extract import extract_from_mysql
from etl.transform import transform_all
from etl.load import load_to_bigquery


def run_pipeline(source: str = "csv"):
    """
    Run the full ETL pipeline.

    Args:
        source: "csv" for CSV files, "mysql" for MySQL database
    """
    print("=" * 60)
    print("  DataFoundation — ETL Pipeline")
    print("=" * 60)
    print()

    start_time = time.time()

    # ── EXTRACT ──
    print("📥 [1/3] EXTRACT")
    print("-" * 40)
    if source == "mysql":
        raw_data = extract_from_mysql()
    print()

    # ── TRANSFORM ──
    print("🔄 [2/3] TRANSFORM")
    print("-" * 40)
    transformed_data = transform_all(raw_data)
    print()

    # ── LOAD ──
    print("📤 [3/3] LOAD")
    print("-" * 40)
    load_to_bigquery(transformed_data)
    print()

    elapsed = time.time() - start_time
    print("=" * 60)
    print(f"  ✅ Pipeline completed in {elapsed:.2f}s")
    print("=" * 60)

    return transformed_data


if __name__ == "__main__":
    source = "mysql" if "--mysql" in sys.argv else "csv"
    run_pipeline(source=source)