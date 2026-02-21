from fastapi import APIRouter
from api.core.bigquery_client import run_query

router = APIRouter(prefix="/api/providers", tags=["Providers"])

from fastapi import HTTPException

@router.get("/")
def list_providers():
    query = """
    SELECT provider_id, provider_name, speciality, organization
    FROM `healthcareproject-488102.healthcare.mart_provider_productivity`
    """
    try:
        result = run_query(query)
        return result
    except Exception as e:
        print("API Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{id}/productivity")
def provider_productivity(id: str):
    query = f"""
    SELECT
        provider_id,
        provider_name,
        speciality,
        organization,
        COUNT(DISTINCT encounter_id) AS total_appointments,
        COUNT(DISTINCT patient_key) AS unique_patients,
        ROUND(AVG(duration_hours), 2) AS avg_duration_hours,
        ROUND(SUM(total_cost), 2) AS total_revenue
    FROM `healthcareproject-488102.healthcare.fact_encounters` e
    JOIN `healthcareproject-488102.healthcare.dim_providers` p
        ON e.provider_key = p.provider_key
    WHERE provider_id = '{id}'
    GROUP BY provider_id, provider_name, speciality, organization
    """
    return run_query(query)
