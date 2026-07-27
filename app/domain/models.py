import datetime
from enum import Enum
from pydantic import BaseModel, Field

### ENUMS ###
class FindingSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    SUGGESTION = "suggestion"

class FindingCategory(str, Enum):
    GRADING = "grading"
    SCHEDULE = "schedule"
    ALIGNMENT = "alignment"
    POLICY = "policy"
    COMPLETENESS = "completeness"

class AuditStatus(str, Enum):
    READY = "ready"
    NEEDS_REVIEW = "needs_review"
    NOT_READY = "not_ready"


# Originally was going to have a plain Assessment model.
# But this won't work if we need to compare due dates & other properties across different sources (ex. syllabus & class schedule)
# Not every source will have weights & due dates --> Both optional.
class AssessmentRecord(BaseModel):
    id: str = Field(description="Stable, unique identifier for the assessment record.")
    name: str = Field(description="Human readable name of the assessment.") 
    source_file: str = Field(description="Source file of the assessment record (ex. syllabus, class schedule).")
    weight: float | None = Field(default = None, description="Weight of the assessment in the source.")
    due_date: datetime.date | None = Field(default = None, description="Due date of the assessment in the source.")
    required_topic_ids: list[str] = Field(description="List of required topic IDs students need for the assessment.")

# A course topic
class CourseTopic(BaseModel):
    id: str = Field(description="Stable, unique identifier for the course topic.")
    name: str = Field(description="Human readable name of the course topic.")
    teaching_date : datetime.date = Field(description="Date when the course topic is taught.")

# Model represents any course document (syllabus, assignment doc, rubrics, etc.)
class CourseDocument(BaseModel):
    source_file: str = Field(description="Source filename of the course document.")
    content: str = Field(description="Original document text (for agents).")

# All information about a course for an audit
class CoursePackage(BaseModel):
    course_name: str = Field(description="Name of the audited course.")
    topics: list[CourseTopic] = Field(description="List of structured course topics taught in the course.")
    assessments: list[AssessmentRecord] = Field(description="List of structured assessment records in the course.")
    documents: list[CourseDocument] = Field(description="List of course documents (syllabus, assignment docs, rubrics, etc.) for the course.")

class AuditEvidence(BaseModel):
    source_file: str = Field(description="Source filename reference for the evidence")
    details: str = Field(description="Relevant facts, values, excerpts, etc. from the source file.")

class AuditFinding(BaseModel):
    severity: FindingSeverity = Field(description="Severity of the finding.")
    category: FindingCategory = Field(description="Category of the finding.")
    evidence: list[AuditEvidence] = Field(description="Evidence supporting this finding.")
    summary: str = Field(description="Short summary for API/Demo purposes.")
    explanation: str = Field(description="Detailed explanation of why the finding matters.")
    recommendation: str = Field(description="Recommended action to address the finding.")
    detected_by: str = Field(description="Name of the agent or code function that detected the finding.")

class AuditReport(BaseModel):
    course_name: str = Field(description="Name of the audited course.")
    audit_status: AuditStatus = Field(description="Status derived from audit findings (existence of critical, warning, or suggestion findings).")
    findings: list[AuditFinding] = Field(description="List of audit findings.")
    generated_at: datetime.datetime = Field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))

# Used to normalize agent output
class AgentAuditResult(BaseModel):
    findings: list[AuditFinding]