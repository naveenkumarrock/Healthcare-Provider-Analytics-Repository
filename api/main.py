from fastapi import FastAPI
from api.routes import providers, appointments, readmissions

app = FastAPI(title="Healthcare Analytics API")

app.include_router(providers.router)
app.include_router(appointments.router)
app.include_router(readmissions.router)