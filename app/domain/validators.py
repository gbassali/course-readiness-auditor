from collections import defaultdict
import datetime

from .models import AssessmentRecord, CoursePackage, AuditFinding, AuditEvidence, FindingCategory, FindingSeverity

# Sums the weights of all assessments in the course package (from the syllabus).
# Returns AuditFinding if the total doesn't equal 100.
def validate_grade_total(course_package: CoursePackage) -> list[AuditFinding]:
    weighted_assessments = [assessment for assessment in course_package.assessments if assessment.weight is not None]
    if not weighted_assessments:
        return []
    total = sum(assessment.weight for assessment in weighted_assessments)

    # Only return a finding if the total is not equal to 100
    if total == 100:
        return []
    else:
        weight_details = ", ".join(
            f"{assessment.name}: {assessment.weight:g}%"
            for assessment in weighted_assessments
        )

        return [
            AuditFinding(
                severity=FindingSeverity.CRITICAL,
                category=FindingCategory.GRADING,
                summary=f"Assessment weights total {total:g}%",
                explanation= "The published assessment weights do not total 100%, so the final-grade calculation is incorrect.",
                recommendation= "Adjust the assessment weights so the published total is 100%.",
                detected_by="validate_grade_total",
                evidence=[
                    AuditEvidence(
                        source_file=weighted_assessments[0].source_file,
                        details=f"Published weights: {weight_details}.\n Total weight: {total:g}%."
                    )
                ],
            )
        ]

def validate_conflicting_due_dates(course_package: CoursePackage) -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    assessments_by_id: dict[str, list[AssessmentRecord]] = defaultdict(list)

    # Group assessment records with due dates by ID
    for assessment in course_package.assessments:
        if assessment.due_date is not None:
            assessments_by_id[assessment.id].append(assessment)

    for assessment_id, assessment_records in assessments_by_id.items():
        # Set of unique due dates for this assessment ID
        unique_date_set = {
            record.due_date
            for record in assessment_records
        }

        if len(unique_date_set) <= 1:
            continue
        else:
            assessment_name = assessment_records[0].name
            findings.append(
                AuditFinding(
                    severity=FindingSeverity.CRITICAL,
                    category=FindingCategory.SCHEDULE,
                    summary=f"{assessment_name} has conflicting due dates",
                    explanation= "Different course documents have different deadlines for the same assessment.",
                    evidence=[
                        AuditEvidence(
                            source_file=record.source_file,
                            details=(
                                f"{assessment_id} due date: "
                                f"{record.due_date.isoformat()}"
                            ),
                        )
                        for record in assessment_records
                    ],
                    recommendation="Select the correct due date and update every course document to use the same deadline.",
                    detected_by="validate_conflicting_due_dates",
                )
            )
    return findings
    
def validate_assignment_topic_sequence(course_package: CoursePackage) -> list[AuditFinding]:
    # Dict mapping each topic ID to its CourseTopic object
    topics_by_id = { topic.id: topic for topic in course_package.topics}
    # Key: assignment ID, due date, required topic ID
    # Group by date too because the same assignment may have different due dates in different sources.
    sequence_records: dict[tuple[str, datetime.date, str], list[AssessmentRecord]] = defaultdict(list)

    for assessment in course_package.assessments:
        if assessment.due_date is None:
            continue

        # Only consider assessments with due dates and required topics. 
        for topic_id in assessment.required_topic_ids:
            sequence_records[(assessment.id, assessment.due_date, topic_id)].append(assessment)

    findings: list[AuditFinding] = []

    for (assessment_id, due_date, topic_id), records in sequence_records.items():
        topic = topics_by_id.get(topic_id)

        if topic is None:
            continue

        if due_date >= topic.teaching_date:
            continue

        assessment_name = records[0].name
        # All source files that reference this assessment ID, due date, and required topic ID
        source_files = [record.source_file for record in records] 

        # Add evidence of the assessment's due date and required topic for each source file
        evidence = [
            AuditEvidence(
                source_file=source_file,
                details= f"{assessment_id} is due on {due_date.isoformat()} and requires topic {topic_id}."
            )
            for source_file in source_files
        ]

        # Add evidence of the topic's teaching date from the course schedule
        evidence.append(
            AuditEvidence(
                source_file="course_schedule.json",
                details= f"{topic.name} ({topic.id}) is taught on {topic.teaching_date.isoformat()}."
            )
        )

        findings.append(
            AuditFinding(
                severity=FindingSeverity.CRITICAL,
                category=FindingCategory.SCHEDULE,
                summary= f"{assessment_name} is due before a required topic is taught",
                explanation= f"Students are expected to apply {topic.name} before the course schedule introduces the topic.",
                evidence=evidence,
                recommendation= "Move the assessment deadline until after the required topic is taught, or teach the topic earlier.",
                detected_by="validate_assignment_topic_sequence",
            )
        )
    return findings