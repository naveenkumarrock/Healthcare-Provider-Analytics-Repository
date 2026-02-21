"""
Load CSV data files into MySQL staging tables (Simple Path Version)
"""

import os
import csv
import sys
import mysql.connector
import uuid
import logging
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# ✅ Simple relative paths
SYNTHEA_DIR = "data/synthea/"
CMS_DIR = "data/hrrp/"

# -------------------- Logging Setup --------------------
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("data_loader.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_connection():
    """Create MySQL connection from environment variables."""
    return mysql.connector.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE", "healthcare_staging"),
    )


def load_csv_to_table(cursor, filepath, table_name, column_mapping, parent_check=None):
    """
    parent_check: optional tuple (parent_table, parent_column, csv_child_column)
    Only insert rows where CSV child_column exists in parent_table.parent_column
    """
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        logger.warning(f"File not found: {filepath}")
        return 0

    # 🔹 Get valid parent keys if parent_check is provided
    valid_parent_keys = None
    if parent_check:
        parent_table, parent_column, csv_child_column = parent_check
        cursor.execute(f"SELECT {parent_column} FROM {parent_table}")
        valid_parent_keys = set(row[0] for row in cursor.fetchall())
        logger.info(f"Filtering rows based on parent table '{parent_table}' ({len(valid_parent_keys)} valid keys)")

    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 🔹 skip row if it doesn't match parent
            if valid_parent_keys and row.get(parent_check[2]) not in valid_parent_keys:
                continue

            values = []
            for db_col, csv_col in column_mapping.items():
                if csv_col is None:
                    values.append(str(uuid.uuid4()))
                else:
                    val = row.get(csv_col)
                    if val:
                        val = val.strip()
                        # Fix ISO 8601 datetime
                        if "datetime" in db_col.lower():
                            val = val.replace("T", " ").replace("Z", "")
                        # Fix DATE format (MM/DD/YYYY -> YYYY-MM-DD)
                        elif "date" in db_col.lower():
                            try:
                                dt = datetime.strptime(val, "%m/%d/%Y")
                                val = dt.strftime("%Y-%m-%d")
                            except ValueError:
                                pass
                        # Convert numeric columns to float or int
                        elif db_col in ["number_of_discharges", "number_of_readmissions",
                                        "expected_readmission_rate", "predicted_readmission_rate",
                                        "excess_readmission_ratio", "total_cost", "cost", "BASE_COST"]:
                            try:
                                val = float(val)
                            except (ValueError, TypeError):
                                val = None  # replace invalid text with NULL
                    values.append(val or None)

            rows.append(tuple(values))

    if not rows:
        print(f"⚠ No data in {filepath} after filtering")
        logger.warning(f"No data in {filepath} after filtering")
        return 0

    db_columns = ", ".join(column_mapping.keys())
    placeholders = ", ".join(["%s"] * len(column_mapping))
    sql = f"INSERT INTO {table_name} ({db_columns}) VALUES ({placeholders})"
    try:
        cursor.executemany(sql, rows)
    except mysql.connector.Error as e:
        logger.error(f"MySQL error while inserting into {table_name}: {e}")
        raise
    return len(rows)


def main():
    print("=" * 50)
    print("MySQL Data Loader (Simple Version)")
    print("=" * 50)
    logger.info("=" * 50)
    logger.info("MySQL Data Loader (Simple Version)")
    logger.info("=" * 50)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("[1] Loading providers...")
        logger.info("[1] Loading providers...")
        count = load_csv_to_table(
            cursor,
            SYNTHEA_DIR + "providers.csv",
            "stg_providers",
            {
                "provider_id": "Id",
                "name": "NAME",
                "gender": "GENDER",
                "speciality": "SPECIALITY",
                "organization": "ORGANIZATION",
                "city": "CITY",
                "state": "STATE",
                "zip": "ZIP"
            },
        )
        conn.commit()
        print(f"✓ {count} providers loaded")
        logger.info(f"✓ {count} providers loaded")

        logger.info("[2] Loading patients...")
        print("[2] Loading patients...")
        count = load_csv_to_table(
            cursor,
            SYNTHEA_DIR + "patients.csv",
            "stg_patients",
            {
                "patient_id": "Id",
                "birthdate": "BIRTHDATE",
                "deathdate": "DEATHDATE",
                "first_name": "FIRST",
                "last_name": "LAST",
                "gender": "GENDER",
                "race": "RACE",
                "ethnicity": "ETHNICITY",
                "city": "CITY",
                "state": "STATE",
                "zip": "ZIP",
                "marital_status": "MARITAL"
            },
        )
        conn.commit()
        print(f"✓ {count} patients loaded")
        logger.info(f"✓ {count} patients loaded")

        logger.info("[3] Loading encounters...")
        print("[3] Loading encounters...")
        count = load_csv_to_table(
            cursor,
            SYNTHEA_DIR + "encounters.csv",
            "stg_encounters",
            {
                "encounter_id": "Id",
                "patient_id": "PATIENT",
                "provider_id": "PROVIDER",
                "encounter_type": "CODE",
                "encounter_class": "ENCOUNTERCLASS",
                "start_datetime": "START",
                "end_datetime": "STOP",
                "total_cost": "TOTAL_CLAIM_COST",
                "reason_code": "REASONCODE",
                "reason_description": "REASONDESCRIPTION"
            },
        )
        conn.commit()
        print(f"✓ {count} encounters loaded")
        logger.info(f"✓ {count} encounters loaded")

        logger.info("[4] Loading conditions (only matched encounters)...")
        print("[4] Loading conditions (only matched encounters)...")
        count = load_csv_to_table(
                cursor,
                SYNTHEA_DIR + "conditions.csv",
                "stg_conditions",
                {
                    "condition_id": None,
                    "patient_id": "PATIENT",
                    "encounter_id": "ENCOUNTER",
                    "code": "CODE",
                    "description": "DESCRIPTION",
                    "onset_date": "START",
                    "abatement_date": "STOP"
                },
                parent_check=("stg_encounters", "encounter_id", "ENCOUNTER")  # only matched
            )
        conn.commit()
        print(f"✓ {count} conditions loaded")
        logger.info(f"✓ {count} conditions loaded")

        logger.info("[5] Loading procedures (only matched encounters)...")
        print("[5] Loading procedures (only matched encounters)...")
        count = load_csv_to_table(
        cursor,
        SYNTHEA_DIR + "procedures.csv",
        "stg_procedures",
        {
            "procedure_id": None,
            "patient_id": "PATIENT",
            "encounter_id": "ENCOUNTER",
            "code": "CODE",
            "description": "DESCRIPTION",
            "performed_datetime": "DATE",
            "cost": "BASE_COST"
        },
        parent_check=("stg_encounters", "encounter_id", "ENCOUNTER")  # only matched
        )
        conn.commit()
        print(f"✓ {count} procedures loaded")
        logger.info(f"✓ {count} procedures loaded")

        logger.info("[6] Loading CMS readmissions...")
        print("[6] Loading CMS readmissions...")
        count = load_csv_to_table(
            cursor,
            CMS_DIR + "FY_2025_Hospital_Readmissions_Reduction_Program_Hospital.csv",
            "stg_hospital_readmissions",
            {
                "hospital_id": "Facility ID",
                "hospital_name": "Facility Name",
                "measure_name": "Measure Name",
                "number_of_discharges": "Number of Discharges",
                "expected_readmission_rate": "Expected Readmission Rate",
                "predicted_readmission_rate": "Predicted Readmission Rate",
                "excess_readmission_ratio": "Excess Readmission Ratio",
                "number_of_readmissions": "Number of Readmissions",
                "start_date": "Start Date",
                "end_date": "End Date"
            },
        )
        conn.commit()
        print(f"✓ {count} readmission records loaded")
        print("\n✅ All data loaded successfully!")
        logger.info(f"✓ {count} readmission records loaded")
        logger.info("\n✅ All data loaded successfully!")

    except mysql.connector.Error as e:
        print(f"❌ MySQL Error: {e}")
        logger.error(f"MySQL Error: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()