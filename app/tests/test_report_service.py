from app.domain.models import AuditEvidence, AuditFinding, AuditReport, AuditStatus, FindingCategory, FindingSeverity
from app.services.report_service import ReportService

def make_finding(
    *,
    summary: str,
    severity: FindingSeverity,
    category: FindingCategory = FindingCategory.SCHEDULE,
    evidence: list[AuditEvidence] | None = None,
    explanation: str = "Original explanation.",
    recommendation: str = "Original recommendation.",
    detected_by: str = "test_detector",
) -> AuditFinding:
    return AuditFinding(
        severity=severity,
        category=category,
        evidence=evidence
        or [
            AuditEvidence(
                source_file="syllabus.md",
                details="Supporting evidence.",
            )
        ],
        summary=summary,
        explanation=explanation,
        recommendation=recommendation,
        detected_by=detected_by,
    )


def make_report(findings: list[AuditFinding]) -> AuditReport:
    return AuditReport(
        course_name="COMP 4000",
        audit_status=AuditStatus.NOT_READY,
        findings=findings,
    )


def test_prepare_report_sorts_findings_by_severity() -> None:
    suggestion = make_finding(summary="Suggestion", severity=FindingSeverity.SUGGESTION)
    first_critical = make_finding(summary="First critical", severity=FindingSeverity.CRITICAL)
    warning = make_finding(summary="Warning", severity=FindingSeverity.WARNING)
    second_critical = make_finding(summary="Second critical", severity=FindingSeverity.CRITICAL)
    report = make_report([suggestion, first_critical, warning, second_critical])

    prepared = ReportService().prepare_report(report)

    assert prepared.findings == [
        first_critical,
        second_critical,
        warning,
        suggestion,
    ]


def test_prepare_report_deduplicates_normalized_summaries() -> None:
    first = make_finding(summary="Conflicting due date!", severity=FindingSeverity.WARNING)
    duplicate = make_finding(summary="  conflicting DUE date.  ", severity=FindingSeverity.WARNING)
    prepared = ReportService().prepare_report(
        make_report([first, duplicate])
    )

    assert len(prepared.findings) == 1
    assert prepared.findings[0].summary == first.summary


def test_duplicate_keeps_higher_severity_and_merges_metadata() -> None:
    warning = make_finding(
        summary="Conflicting due date",
        severity=FindingSeverity.WARNING,
        evidence=[
            AuditEvidence(
                source_file="syllabus.md",
                details="Due date: November 3.",
            )
        ],
        explanation="Warning explanation.",
        recommendation="Warning recommendation.",
        detected_by="validator_a",
    )
    critical = make_finding(
        summary="Conflicting due date.",
        severity=FindingSeverity.CRITICAL,
        evidence=[
            # This is the same evidence as above after whitespace
            # normalization and should not be repeated.
            AuditEvidence(
                source_file="syllabus.md",
                details="Due   date: November 3.",
            ),
            AuditEvidence(
                source_file="course_schedule.json",
                details="Due date: October 27.",
            ),
        ],
        explanation="Critical explanation.",
        recommendation="Critical recommendation.",
        detected_by="validator_a, validator_b",
    )

    prepared = ReportService().prepare_report(
        make_report([warning, critical])
    )

    assert len(prepared.findings) == 1

    merged = prepared.findings[0]
    assert merged.severity == FindingSeverity.CRITICAL
    assert merged.explanation == "Critical explanation."
    assert merged.recommendation == "Critical recommendation."
    assert merged.detected_by == "validator_a, validator_b"
    assert merged.evidence == [
        warning.evidence[0],
        critical.evidence[1],
    ]


def test_same_summary_in_different_categories_is_not_deduplicated() -> None:
    schedule_finding = make_finding(
        summary="Conflicting course information",
        severity=FindingSeverity.CRITICAL,
        category=FindingCategory.SCHEDULE,
    )
    policy_finding = make_finding(
        summary="Conflicting course information",
        severity=FindingSeverity.WARNING,
        category=FindingCategory.POLICY,
    )

    prepared = ReportService().prepare_report(
        make_report([policy_finding, schedule_finding])
    )

    assert prepared.findings == [schedule_finding, policy_finding]


def test_prepare_report_does_not_modify_original_report() -> None:
    warning = make_finding(summary="Warning", severity=FindingSeverity.WARNING)
    critical = make_finding(summary="Critical", severity=FindingSeverity.CRITICAL)
    report = make_report([warning, critical])
    original_findings = list(report.findings)

    prepared = ReportService().prepare_report(report)

    assert prepared is not report
    assert report.findings == original_findings
    assert prepared.findings == [critical, warning]
