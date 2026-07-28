import os
from pathlib import Path
from fastapi import APIRouter

from ..agents.coordinator import create_coordinator
from ..course_package_loader import CoursePackageLoader
from ..domain.models import AuditReport
from ..services.audit_service import AuditService
from ..services.report_service import ReportService
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter


router = APIRouter(prefix="/audits")

# app/api/audits.py -> project root -> sample_course
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_COURSE_PATH = PROJECT_ROOT / "app" / "sample_course"

MODEL_NAME = "google_genai:gemini-3.5-flash-lite"

rate_limiter = InMemoryRateLimiter(
    requests_per_second=1 / 6,  # One request every 20 seconds
    check_every_n_seconds=0.1,
    max_bucket_size=1,           # Do not allow bursts
)

model = init_chat_model(
    MODEL_NAME,
    rate_limiter=rate_limiter,
    max_retries=10,
    timeout=180,
)

# Construct these once instead of recreating them for every HTTP request
coordinator = create_coordinator(model)
audit_service = AuditService(loader=CoursePackageLoader(), coordinator=coordinator)
report_service = ReportService()

@router.post("/run", tags=["audits"], response_model=AuditReport, summary="Run the course-readiness audit")
def run_audit() -> AuditReport:
    report = audit_service.run_audit(SAMPLE_COURSE_PATH)
    return report_service.prepare_report(report)
