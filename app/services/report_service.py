import re
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

from ..domain.models import AuditEvidence, AuditFinding, AuditReport, FindingSeverity


class ReportService:
    SEVERITY_ORDER = {
        FindingSeverity.CRITICAL: 0,
        FindingSeverity.WARNING: 1,
        FindingSeverity.SUGGESTION: 2,
    }

    def prepare_report(self, report: AuditReport) -> AuditReport:
        """
        Return a new report with deduplicated and severity-sorted findings.
        The original report is not modified.
        """
        findings = self._deduplicate_findings(report.findings)

        # Sort findings by severity
        findings.sort(key=lambda finding: self.SEVERITY_ORDER[finding.severity])

        # Replaces report.findings with the deduplicated & sorted findings
        return report.model_copy(update={"findings": findings})

    def render_markdown(self, report: AuditReport) -> str:
        prepared_report = self.prepare_report(report)
        findings = prepared_report.findings

        severity_counts = Counter(finding.severity for finding in findings)
        status = (
            prepared_report.audit_status.value
            .replace("_", " ")
            .title()
        )
        generated_at = prepared_report.generated_at.isoformat(timespec="seconds")

        lines = [
            "# Course Readiness Audit Report",
            "",
            f"**Course:** {prepared_report.course_name}",
            "",
            f"**Audit status:** {status}",
            "",
            f"**Generated:** {generated_at}",
            "",
            "## Summary",
            "",
            "| Severity | Findings |",
            "|---|---:|",
            (
                f"| Critical | "
                f"{severity_counts[FindingSeverity.CRITICAL]} |"
            ),
            (
                f"| Warning | "
                f"{severity_counts[FindingSeverity.WARNING]} |"
            ),
            (
                f"| Suggestion | "
                f"{severity_counts[FindingSeverity.SUGGESTION]} |"
            ),
            f"| **Total** | **{len(findings)}** |",
            "",
            "## Findings",
            "",
        ]

        if not findings:
            lines.extend(["No course-readiness issues were detected.", ""])
            return "\n".join(lines)

        finding_number = 1

        for severity in self.SEVERITY_ORDER:
            severity_findings = [
                finding
                for finding in findings
                if finding.severity == severity
            ]

            if not severity_findings:
                continue

            lines.extend([f"### {severity.value.title()}", ""])

            for finding in severity_findings:
                lines.extend([
                    f"#### {finding_number}. {finding.summary}",
                    "",
                    f"**Category:** {finding.category.value.title()}",
                    "",
                    f"**Detected by:** `{finding.detected_by}`",
                    "",
                    "**Why it matters**",
                    "",
                    finding.explanation,
                    "",
                    "**Evidence**",
                    "",
                ])

                for evidence in finding.evidence:
                    details = " ".join(evidence.details.split())
                    lines.append(f"- **{evidence.source_file}:** {details}")

                lines.extend([
                    "",
                    "**Recommendation**",
                    "",
                    finding.recommendation,
                    "",
                ])

                finding_number += 1

        return "\n".join(lines)

    def write_markdown(self, report: AuditReport, output_path: Path) -> Path:
        markdown = self.render_markdown(report)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")

        return output_path

    def _deduplicate_findings(self, findings: Sequence[AuditFinding]) -> list[AuditFinding]:
        unique_findings: dict[tuple[str, str], AuditFinding] = {}

        for finding in findings:
            key = self._finding_key(finding)
            existing = unique_findings.get(key)

            if existing is None:
                unique_findings[key] = finding
                continue

            # If duplicate findings disagree on severity, preserve the more severe version.
            selected = existing

            if (self.SEVERITY_ORDER[finding.severity] < self.SEVERITY_ORDER[existing.severity]):
                selected = finding

            unique_findings[key] = selected.model_copy(
                update={
                    "evidence": self._merge_evidence(
                        existing.evidence,
                        finding.evidence,
                    ),
                    "detected_by": self._merge_detected_by(
                        existing.detected_by,
                        finding.detected_by,
                    ),
                }
            )

        return list(unique_findings.values())

    @staticmethod
    def _finding_key(finding: AuditFinding) -> tuple[str, str]:
        normalized_summary = re.sub(r"[^a-z0-9]+", " ", finding.summary.casefold()).strip()
        return (
            finding.category.value,
            normalized_summary,
        )

    @staticmethod
    def _merge_evidence(*evidence_groups: list[AuditEvidence]) -> list[AuditEvidence]:
        merged: list[AuditEvidence] = []
        seen: set[tuple[str, str]] = set()

        for evidence_group in evidence_groups:
            for evidence in evidence_group:
                key = (
                    evidence.source_file,
                    " ".join(evidence.details.split()),
                )

                if key not in seen:
                    seen.add(key)
                    merged.append(evidence)

        return merged

    @staticmethod
    def _merge_detected_by(*values: str) -> str:
        detectors: list[str] = []

        for value in values:
            for detector in value.split(","):
                detector = detector.strip()

                if detector and detector not in detectors:
                    detectors.append(detector)

        return ", ".join(detectors)
