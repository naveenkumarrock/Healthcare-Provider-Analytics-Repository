from fastapi import APIRouter, HTTPException
from api.core.bigquery_client import run_query

router = APIRouter(prefix="/api/providers", tags=["Providers"])

@router.get("/")
def list_providers():
    """
    Returns all provider productivity metrics for Streamlit dashboard
    """
    query = """
    SELECT 
        provider_key,
        provider_id,
        INITCAP(TRIM(REGEXP_REPLACE(provider_name, r'\\d+', ''))) AS provider_name,
        speciality,
        -- Use COALESCE to ensure no nulls
        COALESCE(ROUND(total_encounters,0), 0) AS total_encounters,
        COALESCE(unique_patients, 0) AS unique_patients,
        COALESCE(ROUND(avg_encounter_duration_hrs, 2), 0) AS avg_encounter_duration_hrs,
        COALESCE(ROUND(total_revenue, 2), 0) AS total_revenue,
        COALESCE(ROUND(avg_cost_per_encounter, 2), 0) AS avg_cost_per_encounter,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', first_encounter) AS first_encounter,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', last_encounter) AS last_encounter
    FROM `healthcareproject-488102.healthcare.mart_provider_productivity`
    """
    try:
        result = run_query(query)
        # Ensure result is a list of dicts
        return [dict(row) for row in result]
    except Exception as e:
        print("API Error:", e)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{id}/productivity")
def provider_productivity(id: str):
    query = f"""
    SELECT
        p.provider_id,
        INITCAP(TRIM(REGEXP_REPLACE(p.provider_name, r'\\d+', ''))) AS provider_name,
        p.speciality,
        p.organization,
        e.encounter_class,
        COUNT(DISTINCT e.encounter_id) AS total_appointments,
        COUNT(DISTINCT e.patient_key) AS unique_patients,
        ROUND(AVG(e.duration_hours), 2) AS avg_duration_hours,
        ROUND(SUM(e.total_cost), 2) AS total_revenue,
        ROUND(SUM(e.total_cost)/NULLIF(COUNT(DISTINCT e.encounter_id),0), 2) AS avg_cost_per_encounter,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', MIN(e.encounter_datetime)) AS first_encounter,
        FORMAT_TIMESTAMP('%Y-%m-%d %H:%M:%S', MAX(e.encounter_datetime)) AS last_encounter
    FROM `healthcareproject-488102.healthcare.fact_encounters` e
    JOIN `healthcareproject-488102.healthcare.dim_providers` p
        ON e.provider_key = p.provider_key
    WHERE p.provider_id = '{id}'
    GROUP BY p.provider_id, provider_name, p.speciality, p.organization, e.encounter_class
    """
    try:
        result = run_query(query)
        return [dict(row) for row in result]
    except Exception as e:
        print("API Error:", e)
        raise HTTPException(status_code=500, detail=str(e))