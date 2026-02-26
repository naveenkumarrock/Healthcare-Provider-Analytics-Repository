# 🏥 DataFoundation: Healthcare Provider Analytics Repository

An end-to-end healthcare provider analytics system integrating synthetic patient records (Synthea-format) and CMS Hospital Readmissions data. Built with a modern data stack: **Python ETL → MySQL Staging → BigQuery Warehouse → FastAPI REST API → Streamlit Dashboard**.

---

## 📐 Architecture

```
┌──────────────┐   ┌──────────────┐
│ Synthea CSVs │   │  CMS CSVs    │
└──────┬───────┘   └──────┬───────┘
       │                  │
       ▼                  ▼
┌─────────────────────────────────┐
│     Python ETL Pipeline         │
│  (Extract → Transform → Load)  │
└──────┬──────────────┬───────────┘
       │              │
       ▼              ▼
┌────────────┐  ┌──────────────┐
│   MySQL    │  │   BigQuery   │
│  Staging   │  │  Warehouse   │
└─────┬──────┘  └──────┬───────┘
      │                │
      ▼                ▼
┌─────────────────────────────────┐
│       FastAPI REST API          │
│  /providers  /appointments      │
│  /readmissions  /health         │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│     Streamlit Dashboard         │
│  Overview │ Providers │ Appts   │
│        Readmissions             │
└─────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone <repo-url>
cd REVATURE_PROJECT
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
copy .env.example .env
# Edit .env with your MySQL and BigQuery credentials
```

### 3. Create Database Schema in MySQL

```bash
mysql -u root -p < db/mysql_schema.sql
```

### 4. Load Data into MySQL (Staging DB)

```bash
python etl/load/load_to_mysql.py
```

### 5. Run ETL Pipeline (MySQL → BigQuery)

```bash
python -m etl/transform/pipeline.py
```

### 5. Start the REST API

```bash
uvicorn api.main:app --reload
```

### 6. Launch the Dashboard

```bash
streamlit run dashboard/app.py
```

---

## 📂 Project Structure

```
DataFoundation/
├── api/                    # FastAPI REST API
│   ├── main.py
│   ├── core/
|   |   |── bigquery_client.py
│   └── routes/
│       ├── providers.py
│       ├── appointments.py
│       └── readmissions.py
├── dashboard/              # Streamlit Dashboard
│   └── app.py
├── data/                   # Raw data files
│   ├── synthea/
│   └── cms/
├── db/                     # Database schemas
│   └── mysql_schema.sql
├── etl/                    # ETL pipeline
│   ├── extract.py
│   ├── transform.py
│   ├── load_to_bigquery.py
│   |── load_to_mysql.py
│   └── pipeline.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠 Tech Stack

| Layer           | Technology         | Purpose                    |
| --------------- | ------------------ | -------------------------- |
| Staging DB      | MySQL 8.0          | Raw data staging           |
| Warehouse       | GCP BigQuery       | Star schema & data marts   |
| ETL             | Python / Pandas    | Extract, transform, load   |
| REST API        | FastAPI / Uvicorn  | Analytics endpoints        |
| Dashboard       | Streamlit / Plotly | Interactive visualizations |
| Version Control | Git                | Source code management     |

---

## 📊 Data Marts

- **Provider Productivity**: Encounters per provider, avg duration, patient volume, specialty breakdown
- **Appointment Analytics**: Trends over time, encounter type distribution, utilization rates

---

## 📄 License

This project uses synthetic data only. No real PHI is used. For educational and demonstration purposes.
