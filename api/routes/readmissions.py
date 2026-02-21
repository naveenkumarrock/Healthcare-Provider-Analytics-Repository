from fastapi import APIRouter
from api.core.bigquery_client import run_query

router = APIRouter(prefix="/api/readmissions", tags=["Readmissions"])

@router.get("/rates")
def readmission_rates():
    query = """
    SELECT
        hospital_id,
        hospital_name,
        excess_readmission_ratio AS readmission_rate,
        measure_name,
    FROM `healthcareproject-488102.healthcare.fact_readmissions`
    """
    return run_query(query)


# GET /api/readmissions/stats
@router.get("/stats")
def readmission_stats():
    query = """
    SELECT
        ROUND(AVG(excess_readmission_ratio), 2) AS avg_ratio,
        SUM(number_of_readmissions) AS total_readmissions,
        SUM(number_of_discharges) AS total_discharges
    FROM `healthcareproject-488102.healthcare.fact_readmissions`
    """
    return run_query(query)