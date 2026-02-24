import os
import pandas as pd
from dotenv import load_dotenv
from urllib.parse import quote_plus
import sqlalchemy

load_dotenv()

def _get_mysql_connection_string():
    host = os.getenv("MYSQL_HOST", "localhost")
    port = os.getenv("MYSQL_PORT", "3306")
    user = os.getenv("MYSQL_USER", "root")
    password = quote_plus(os.getenv("MYSQL_PASSWORD", ""))
    database = os.getenv("MYSQL_DATABASE", "healthcare_staging")
    return f"mysql+mysqlconnector://{user}:{password}@{host}:{port}/{database}"


def extract_from_mysql():
    """Extract all staging tables from MySQL into DataFrames."""
    conn_str = _get_mysql_connection_string()
    engine = sqlalchemy.create_engine(conn_str)

    print("Extracting from MySQL...")
    data = {
        "providers": pd.read_sql("SELECT * FROM stg_providers", engine),
        "patients": pd.read_sql("SELECT * FROM stg_patients", engine),
        "encounters": pd.read_sql("SELECT * FROM stg_encounters", engine),
        "conditions": pd.read_sql("SELECT * FROM stg_conditions", engine),
        "procedures": pd.read_sql("SELECT * FROM stg_procedures", engine),
        "organizations": pd.read_sql("SELECT * FROM stg_organizations", engine),
        "readmissions": pd.read_sql("SELECT * FROM stg_hospital_readmissions", engine),
    }
    engine.dispose()
    print("✓ Extraction complete")
    return data


if __name__ == "__main__":
    dfs = extract_from_mysql()
    for name, df in dfs.items():
        print(f"{name}: {len(df)} rows")