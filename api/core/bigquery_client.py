from google.cloud import bigquery
from google.oauth2 import service_account

# 🔹 FULL path to your service account file
SERVICE_ACCOUNT_FILE = r"C:\Users\navee\OneDrive\Desktop\Revature_Project\config\healthcareproject-488102-e1bec26d4ec5.json"

# 🔹 Create credentials
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
)

# 🔹 Create BigQuery client
client = bigquery.Client(
    credentials=credentials,
    project=credentials.project_id,
)

def run_query(query: str):
    query_job = client.query(query)
    return [dict(row) for row in query_job.result()]