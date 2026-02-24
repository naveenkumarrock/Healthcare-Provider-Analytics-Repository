from fastapi import APIRouter, HTTPException
from api.core.bigquery_client import run_query

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])

# -------------------- /analytics --------------------
@router.get("/analytics")
def appointment_analytics():
    query = """
    SELECT
        d.year,
        d.month,
        e.encounter_class,
        e.encounter_type,
        COUNT(*) AS total_appointments,
        COUNT(DISTINCT e.patient_key) AS unique_patients,
        ROUND(AVG(e.duration_hours), 2) AS avg_duration,
        ROUND(SUM(e.total_cost), 2) AS total_cost
    FROM `healthcareproject-488102.healthcare.fact_encounters` e
    JOIN `healthcareproject-488102.healthcare.dim_date` d
        ON e.date_key = d.date_key
    GROUP BY d.year, d.month, e.encounter_class, e.encounter_type
    ORDER BY d.year, d.month, e.encounter_class, e.encounter_type
    """
    try:
        result = run_query(query)
        # Ensure each row is a dict
        return [dict(row) for row in result]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- /summary --------------------
@router.get("/summary")
def appointment_summary():
    query = """
    SELECT
        COUNT(*) AS total_encounters,
        COUNT(DISTINCT patient_key) AS unique_patients,
        COUNT(DISTINCT provider_key) AS unique_providers,
        ROUND(AVG(duration_hours), 2) AS avg_duration,
        ROUND(SUM(total_cost), 2) AS total_cost,
        MIN(start_datetime) AS first_appointment,
        MAX(end_datetime) AS last_appointment
    FROM `healthcareproject-488102.healthcare.fact_encounters`
    """
    try:
        result = run_query(query)
        # Return a single dict in a list
        return [dict(result[0])] if result else [{}]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -------------------- /reasons --------------------
@router.get("/reasons")
def appointment_reasons():
    query = """
    SELECT
        reason_code,
        reason_description,
        COUNT(*) AS total_appointments,
        COUNT(DISTINCT patient_key) AS unique_patients,
        ROUND(SUM(total_cost),2) AS total_cost
    FROM `healthcareproject-488102.healthcare.fact_encounters`
    GROUP BY reason_code, reason_description
    ORDER BY total_appointments DESC
    """
    try:
        result = run_query(query)
        return [dict(row) for row in result] if result else []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))