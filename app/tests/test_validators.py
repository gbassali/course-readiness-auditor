from datetime import date
from ..domain.models import CoursePackage, AssessmentRecord, CourseTopic, AuditFinding, AuditEvidence, FindingCategory, FindingSeverity
from ..domain.validators import validate_grade_total, validate_conflicting_due_dates, validate_assignment_topic_sequence

### HELPER FUNCTIONS FOR TESTS ###

def make_course_package(assessments: list[AssessmentRecord] = None, topics: list[CourseTopic] = None) -> CoursePackage:
    """Create a minimal package for validator unit tests."""
    return CoursePackage(
        course_name="Test Course",
        assessments=assessments or [],
        topics=topics or [],
        documents=[],
    )

def make_assessment(assessment_id: str, *, name: str = "Test Assignment", source_file: str = "syllabus.md", weight: float = None, due_date: date = None, required_topic_ids: list[str] = None) -> AssessmentRecord:
    """Create an assessment while keeping individual tests compact."""
    return AssessmentRecord(
        id=assessment_id,
        name=name,
        source_file=source_file,
        weight=weight,
        due_date=due_date,
        required_topic_ids=required_topic_ids or [],
    )

### TESTS ###

def test_grade_total_returns_finding_when_total_is_105() -> None:
    course_package = make_course_package(
        assessments=[
            make_assessment("assignment-1", name="Assignment 1", weight=20),
            make_assessment("assignment-2", name="Assignment 2", weight=30),
            make_assessment("midterm", name="Midterm", weight=25),
            make_assessment("final", name="Final Exam", weight=30),
        ]
    )

    findings = validate_grade_total(course_package)

    assert len(findings) == 1

    finding = findings[0]
    assert isinstance(finding, AuditFinding)
    assert finding.severity == FindingSeverity.CRITICAL
    assert finding.category == FindingCategory.GRADING
    assert "105%" in finding.summary
    assert finding.detected_by == "validate_grade_total"

    assert len(finding.evidence) == 1
    assert finding.evidence[0].source_file == "syllabus.md"
    assert "105%" in finding.evidence[0].details

def test_grade_total_returns_no_finding_when_total_is_100() -> None:
    course_package = make_course_package(
        assessments=[
            make_assessment("assignment-1", weight=20),
            make_assessment("assignment-2", weight=30),
            make_assessment("midterm", weight=20),
            make_assessment("final", weight=30),
        ]
    )

    findings = validate_grade_total(course_package)
    assert findings == []

def test_conflicting_due_dates_returns_finding() -> None:
    course_package = make_course_package(
        assessments=[
            make_assessment(
                "assignment-2",
                name="Relational Data Service",
                source_file="syllabus.md",
                due_date=date(2026, 11, 3),
            ),
            make_assessment(
                "assignment-2",
                name="Relational Data Service",
                source_file="course_schedule.json",
                due_date=date(2026, 10, 27),
            ),
        ]
    )

    findings = validate_conflicting_due_dates(course_package)

    assert len(findings) == 1

    finding = findings[0]
    assert finding.severity == FindingSeverity.CRITICAL
    assert finding.category == FindingCategory.SCHEDULE
    assert "conflicting due dates" in finding.summary
    assert finding.detected_by == "validate_conflicting_due_dates"

    evidence_sources = { evidence.source_file for evidence in finding.evidence }
    assert evidence_sources == {"syllabus.md", "course_schedule.json"}

def test_matching_due_dates_returns_no_finding() -> None:
    shared_due_date = date(2026, 11, 3)

    course_package = make_course_package(
        assessments=[
            make_assessment(
                "assignment-2",
                source_file="syllabus.md",
                due_date=shared_due_date,
            ),
            make_assessment(
                "assignment-2",
                source_file="course_schedule.json",
                due_date=shared_due_date,
            ),
        ]
    )

    findings = validate_conflicting_due_dates(course_package)
    assert findings == []

def test_assignment_due_before_required_topic_returns_finding() -> None:
    course_package = make_course_package(
        topics=[
            CourseTopic(
                id="database-normalization",
                name="Relational Database Normalization",
                teaching_date=date(2026, 10, 29),
            )
        ],
        assessments=[
            make_assessment(
                "assignment-2",
                name="Relational Data Service",
                source_file="course_schedule.json",
                due_date=date(2026, 10, 27),
                required_topic_ids=["database-normalization"],
            )
        ],
    )

    findings = validate_assignment_topic_sequence(course_package)
    assert len(findings) == 1

    finding = findings[0]
    assert finding.severity == FindingSeverity.CRITICAL
    assert finding.category == FindingCategory.SCHEDULE
    assert "before a required topic is taught" in finding.summary
    assert finding.detected_by == "validate_assignment_topic_sequence"

    evidence_details = " ".join(evidence.details for evidence in finding.evidence)

    assert "2026-10-27" in evidence_details
    assert "2026-10-29" in evidence_details
    assert "database-normalization" in evidence_details

def test_assignment_due_after_required_topic_returns_no_finding() -> None:
    course_package = make_course_package(
        topics=[
            CourseTopic(
                id="database-normalization",
                name="Relational Database Normalization",
                teaching_date=date(2026, 10, 29),
            )
        ],
        assessments=[
            make_assessment(
                "assignment-2",
                due_date=date(2026, 11, 3),
                required_topic_ids=["database-normalization"],
            )
        ],
    )

    findings = validate_assignment_topic_sequence(course_package)
    assert findings == []