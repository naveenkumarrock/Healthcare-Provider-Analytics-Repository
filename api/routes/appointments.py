from fastapi import APIRouter
from api.core.bigquery_client import run_query

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

# GET /api/appointments/analytics
@router.get("/analytics")
def appointment_analytics():
    query = """
    SELECT
    d.year,
    d.month,
    e.encounter_type,
    COUNT(*) AS total_appointments,
    COUNT(DISTINCT e.patient_key) AS unique_patients
    FROM `healthcareproject-488102.healthcare.fact_encounters` e
    JOIN `healthcareproject-488102.healthcare.dim_date` d
    ON e.date_key = d.date_key
    GROUP BY d.year, d.month, e.encounter_type
    """
    return run_query(query)


# GET /api/appointments/summary
@router.get("/summary")
def appointment_summary():
    query = """
    SELECT
        COUNT(*) AS total_encounters,
        COUNT(DISTINCT patient_key) AS unique_patients,
        COUNT(DISTINCT provider_key) AS unique_providers,
        ROUND(AVG(duration_hours), 2) AS avg_duration,
        ROUND(SUM(total_cost), 2) AS total_cost
    FROM `healthcareproject-488102.healthcare.fact_encounters`
    """
    return run_query(query)