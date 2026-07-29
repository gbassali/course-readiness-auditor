from pathlib import Path
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.rate_limiters import InMemoryRateLimiter
from ..course_package_loader import CoursePackageLoader
from ..agents.coordinator import create_coordinator
from ..services.audit_service import AuditService
from ..services.report_service import ReportService

load_dotenv()

rate_limiter = InMemoryRateLimiter(
    requests_per_second=1 / 6,  # One request every 10 seconds
    check_every_n_seconds=0.1,
    max_bucket_size=1,           # Do not allow bursts
)

model = init_chat_model(
    "google_genai:gemini-3.5-flash-lite",
    rate_limiter=rate_limiter,
    max_retries=10,
    timeout=180,
)

report_service = ReportService()
audit_service = AuditService(
    loader=CoursePackageLoader(),
    coordinator=create_coordinator(model=model)
)

report = audit_service.run_audit(Path("C:\\Users\\gurle\\Personal Projects\\prototype\\course-readiness-auditor\\app\\sample_course"))
# print(report.model_dump_json(indent=2))

report = report_service.prepare_report(report)
report_path = report_service.write_markdown(report, Path("generated/audit_report.md"))
print(f"Report written to {report_path}")