from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()  # Load environment variables from .env file
from .api.audits import router as audits_router

app = FastAPI(
    title="Course Readiness Auditor",
    description="Audits a prepared course package for readiness issues.",
    version="0.1.0",
)
app.include_router(audits_router)
