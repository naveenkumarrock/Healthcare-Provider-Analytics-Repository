"""
Load transformed DataFrames into Google BigQuery.
Falls back to local Parquet storage when BigQuery credentials are unavailable.
"""

import os
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "warehouse"


def load_to_bigquery(transformed_data: dict):
    """Load all transformed DataFrames to BigQuery or local Parquet fallback."""
    project_id = os.getenv("GCP_PROJECT_ID")
    dataset_id = os.getenv("GCP_DATASET_ID", "healthcare")

    if project_id:
        _load_to_bq(transformed_data, project_id, dataset_id)
    else:
        print("  ⚠ BigQuery credentials not configured, using local Parquet fallback...")
        _load_to_parquet(transformed_data)


def _load_to_bq(data: dict, project_id: str, dataset_id: str):
    """Load DataFrames to BigQuery tables."""
    try:
        from google.cloud import bigquery

        client = bigquery.Client(project=project_id)

        # Create dataset if it doesn't exist
        dataset_ref = f"{project_id}.{dataset_id}"
        try:
            client.get_dataset(dataset_ref)
        except Exception:
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            client.create_dataset(dataset, exists_ok=True)
            print(f"  ✓ Created BigQuery dataset: {dataset_ref}")

        for table_name, df in data.items():
            table_id = f"{project_id}.{dataset_id}.{table_name}"
            job_config = bigquery.LoadJobConfig(
                write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
                autodetect=True,
            )

            # Handle datetime columns
            for col in df.select_dtypes(include=["datetime64"]).columns:
                df[col] = df[col].dt.tz_localize(None)

            job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Wait for completion
            print(f"    ✓ {table_name}: {len(df)} rows → {table_id}")

        print("  ✅ All tables loaded to BigQuery!")

    except Exception as e:
        print(f"  ❌ BigQuery load failed: {e}")
        print("  Falling back to local Parquet storage...")
        _load_to_parquet(data)


def _load_to_parquet(data: dict):
    """Save DataFrames as Parquet files locally (fallback)."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for table_name, df in data.items():
        filepath = OUTPUT_DIR / f"{table_name}.parquet"

        # Convert datetime for parquet compatibility
        for col in df.select_dtypes(include=["datetime64"]).columns:
            df[col] = df[col].dt.tz_localize(None)

        df.to_parquet(filepath, index=False)
        print(f"    ✓ {table_name}: {len(df)} rows → {filepath.name}")

    print(f"  ✅ All tables saved to {OUTPUT_DIR}")