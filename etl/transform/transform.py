"""
Transform module: Clean data, calculate healthcare metrics, build star schema tables.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def transform_all(raw_data: dict) -> dict:
    """
    Apply all transformations to raw extracted data.
    Returns a dict of DataFrames ready for BigQuery loading.
    """
    print("  Running transformations...")

    # Build dimensions
    dim_providers = build_dim_providers(raw_data["providers"])
    dim_patients = build_dim_patients(raw_data["patients"])
    dim_conditions = build_dim_conditions(raw_data["conditions"])
    dim_date = build_dim_date(raw_data["encounters"])

    # Build facts
    fact_encounters = build_fact_encounters(raw_data["encounters"], dim_providers, dim_patients, dim_date)
    fact_procedures = build_fact_procedures(raw_data["procedures"], dim_patients, dim_date)
    fact_readmissions = build_fact_readmissions(raw_data["readmissions"])

    # Build data marts
    mart_provider_productivity = build_mart_provider_productivity(fact_encounters, dim_providers)
    mart_appointment_analytics = build_mart_appointment_analytics(fact_encounters, dim_date)

    transformed = {
        "dim_providers": dim_providers,
        "dim_patients": dim_patients,
        "dim_conditions": dim_conditions,
        "dim_date": dim_date,
        "fact_encounters": fact_encounters,
        "fact_procedures": fact_procedures,
        "fact_readmissions": fact_readmissions,
        "mart_provider_productivity": mart_provider_productivity,
        "mart_appointment_analytics": mart_appointment_analytics,
    }

    for name, df in transformed.items():
        print(f"    ✓ {name}: {len(df)} rows, {len(df.columns)} cols")

    return transformed


# ---- Dimension Builders ----

def build_dim_providers(providers_df: pd.DataFrame) -> pd.DataFrame:
    """Build provider dimension table."""
    dim = providers_df.copy()
    dim = dim.rename(columns={"provider_id": "provider_key"})
    dim["provider_id"] = dim["provider_key"]
    # Clean specialty field
    dim["speciality"] = dim["speciality"].fillna("Unknown")
    dim["organization"] = dim["organization"].fillna("Unknown")
    return dim


def build_dim_patients(patients_df: pd.DataFrame) -> pd.DataFrame:
    """Build patient dimension with derived fields."""
    dim = patients_df.copy()
    dim = dim.rename(columns={"patient_id": "patient_key"})
    dim["patient_id"] = dim["patient_key"]

    # Create full name
    dim["full_name"] = dim["first_name"].fillna("") + " " + dim["last_name"].fillna("")
    dim["full_name"] = dim["full_name"].str.strip()

    # Calculate age
    dim["birthdate"] = pd.to_datetime(dim["birthdate"], errors="coerce")
    today = pd.Timestamp.now()
    dim["age"] = dim["birthdate"].apply(
        lambda x: int((today - x).days / 365.25) if pd.notna(x) else None
    )

    # Clean fields
    dim["gender"] = dim["gender"].fillna("Unknown")
    dim["race"] = dim["race"].fillna("Unknown")
    dim["ethnicity"] = dim["ethnicity"].fillna("Unknown")
    dim["marital_status"] = dim["marital_status"].fillna("Unknown")

    return dim


def build_dim_conditions(conditions_df: pd.DataFrame) -> pd.DataFrame:
    """Build condition dimension (unique codes)."""
    dim = conditions_df[["code", "description"]].drop_duplicates().reset_index(drop=True)
    dim["condition_key"] = dim["code"]
    return dim[["condition_key", "code", "description"]]


def build_dim_date(encounters_df: pd.DataFrame) -> pd.DataFrame:
    """Build date dimension from encounter dates."""
    encounters_df["start_datetime"] = pd.to_datetime(encounters_df["start_datetime"], errors="coerce")
    dates = encounters_df["start_datetime"].dropna().dt.date.unique()
    dates = sorted(dates)

    records = []
    for d in dates:
        dt = pd.Timestamp(d)
        records.append({
            "date_key": int(dt.strftime("%Y%m%d")),
            "full_date": d,
            "year": dt.year,
            "quarter": dt.quarter,
            "month": dt.month,
            "month_name": dt.strftime("%B"),
            "week": dt.isocalendar()[1],
            "day_of_week": dt.dayofweek,
            "day_name": dt.strftime("%A"),
            "is_weekend": dt.dayofweek >= 5,
        })

    return pd.DataFrame(records)


# ---- Fact Builders ----

def build_fact_encounters(encounters_df, dim_providers, dim_patients, dim_date):
    """Build encounter fact table with calculated duration."""
    fact = encounters_df.copy()

    fact["start_datetime"] = pd.to_datetime(fact["start_datetime"], errors="coerce")
    fact["end_datetime"] = pd.to_datetime(fact["end_datetime"], errors="coerce")

    # Calculate duration in hours
    fact["duration_hours"] = (
        (fact["end_datetime"] - fact["start_datetime"]).dt.total_seconds() / 3600
    ).round(2)

    # Create keys
    fact["patient_key"] = fact["patient_id"]
    fact["provider_key"] = fact["provider_id"]
    fact["date_key"] = fact["start_datetime"].dt.strftime("%Y%m%d").astype(int)

    # Cast cost
    fact["total_cost"] = pd.to_numeric(fact["total_cost"], errors="coerce").fillna(0)

    columns = [
        "encounter_id", "patient_key", "provider_key", "date_key",
        "encounter_type", "encounter_class", "start_datetime", "end_datetime",
        "duration_hours", "total_cost", "reason_code", "reason_description"
    ]
    return fact[columns]


def build_fact_procedures(procedures_df, dim_patients, dim_date):
    """Build procedure fact table."""
    fact = procedures_df.copy()
    fact["performed_datetime"] = pd.to_datetime(fact["performed_datetime"], errors="coerce")
    fact["patient_key"] = fact["patient_id"]
    fact["date_key"] = fact["performed_datetime"].dt.strftime("%Y%m%d").astype(int)
    fact["cost"] = pd.to_numeric(fact["cost"], errors="coerce").fillna(0)

    columns = ["procedure_id", "patient_key", "encounter_id", "date_key",
               "code", "description", "performed_datetime", "cost"]
    return fact[columns]


def build_fact_readmissions(readmissions_df):
    """Build readmissions fact table."""
    fact = readmissions_df.copy()
    fact["readmission_id"] = range(1, len(fact) + 1)

    numeric_cols = ["number_of_discharges", "expected_readmission_rate",
                    "predicted_readmission_rate", "excess_readmission_ratio",
                    "number_of_readmissions"]
    for col in numeric_cols:
        fact[col] = pd.to_numeric(fact[col], errors="coerce").fillna(0)

    fact["start_date"] = pd.to_datetime(fact["start_date"], errors="coerce")
    fact["end_date"] = pd.to_datetime(fact["end_date"], errors="coerce")

    columns = ["readmission_id", "hospital_id", "hospital_name", "measure_name",
               "number_of_discharges", "expected_readmission_rate",
               "predicted_readmission_rate", "excess_readmission_ratio",
               "number_of_readmissions", "start_date", "end_date"]
    return fact[columns]


# ---- Data Mart Builders ----

def build_mart_provider_productivity(fact_encounters, dim_providers):
    """Build provider productivity data mart."""
    agg = fact_encounters.groupby("provider_key").agg(
        total_encounters=("encounter_id", "count"),
        unique_patients=("patient_key", "nunique"),
        avg_encounter_duration_hrs=("duration_hours", "mean"),
        total_revenue=("total_cost", "sum"),
        avg_cost_per_encounter=("total_cost", "mean"),
        first_encounter=("start_datetime", "min"),
        last_encounter=("start_datetime", "max"),
    ).reset_index()

    # Round numeric columns
    agg["avg_encounter_duration_hrs"] = agg["avg_encounter_duration_hrs"].round(2)
    agg["total_revenue"] = agg["total_revenue"].round(2)
    agg["avg_cost_per_encounter"] = agg["avg_cost_per_encounter"].round(2)

    # Merge provider details
    provider_cols = ["provider_key", "provider_id", "name", "speciality", "organization"]
    existing_cols = [c for c in provider_cols if c in dim_providers.columns]
    mart = agg.merge(dim_providers[existing_cols], on="provider_key", how="left")

    mart = mart.rename(columns={"name": "provider_name"})
    return mart


def build_mart_appointment_analytics(fact_encounters, dim_date):
    """Build appointment analytics data mart."""
    merged = fact_encounters.merge(dim_date, on="date_key", how="left")

    agg = merged.groupby(["year", "quarter", "month", "month_name",
                           "encounter_type", "encounter_class"]).agg(
        encounter_count=("encounter_id", "count"),
        unique_patients=("patient_key", "nunique"),
        unique_providers=("provider_key", "nunique"),
        avg_duration_hrs=("duration_hours", "mean"),
        total_cost=("total_cost", "sum"),
        avg_cost=("total_cost", "mean"),
    ).reset_index()

    agg["avg_duration_hrs"] = agg["avg_duration_hrs"].round(2)
    agg["total_cost"] = agg["total_cost"].round(2)
    agg["avg_cost"] = agg["avg_cost"].round(2)

    return agg