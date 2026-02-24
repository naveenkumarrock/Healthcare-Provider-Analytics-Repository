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
        readmission_id,
        measure_name,
        number_of_discharges,
        expected_readmission_rate,
        predicted_readmission_rate,
        number_of_readmissions,
        start_date,
        end_date,
    FROM `healthcareproject-488102.healthcare.fact_readmissions`
    """
    return run_query(query)


# GET /api/readmissions/stats
@router.get("/stats")
def readmission_stats():
    query = """
    SELECT
        readmission_id,
        hospital_id,
        hospital_name,
        measure_name,
        number_of_discharges,
        expected_readmission_rate,
        predicted_readmission_rate,
        excess_readmission_ratio,
        number_of_readmissions,
        start_date,
        end_date,
        ROUND(AVG(excess_readmission_ratio), 2) AS avg_ratio,
        SUM(number_of_readmissions) AS total_readmissions,
        SUM(number_of_discharges) AS total_discharges
    FROM `healthcareproject-488102.healthcare.fact_readmissions`
    """
    return run_query(query)