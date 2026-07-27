from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol

from ..agents.coordinator import build_complete_semantic_audit_request
from ..domain.models import AgentAuditResult, AuditFinding, AuditReport, AuditStatus, CoursePackage, FindingSeverity
from ..domain.validators import validate_assignment_topic_sequence, validate_conflicting_due_dates, validate_grade_total
from ..course_package_loader import CoursePackageLoader

# A callable is any object that can be called using ()
# All validators take in a CoursePackage & return a list of AuditFindings.
# Syntax: Callable[[Arg1Type, Arg2Type, ...], ReturnType]
Validator = Callable[[CoursePackage], list[AuditFinding]]

DEFAULT_VALIDATORS: tuple[Validator, ...] = (
    validate_grade_total,
    validate_conflicting_due_dates,
    validate_assignment_topic_sequence,
)

# Protocol class: Any class with the following methods/attributes works. 
class CoordinatorInvoker(Protocol):
    def invoke(self, input: dict[str, Any]) -> dict[str, Any]:
        ...

class AuditService:
    def __init__(self, loader: CoursePackageLoader, coordinator: CoordinatorInvoker, validators: Sequence[Validator] = DEFAULT_VALIDATORS):
        self._loader = loader
        self._coordinator = coordinator
        self._validators = tuple(validators)

    def run_audit(self, course_package_path: Path) -> AuditReport:
        course_package = self._loader.load_course_package(course_package_path)

        deterministic_findings = self._run_deterministic_validators(course_package)
        semantic_findings = self._run_semantic_audit(course_package)

        findings = [
            *deterministic_findings,
            *semantic_findings,
        ]

        return AuditReport(
            course_name=course_package.course_name,
            audit_status=self._determine_status(findings),
            findings=findings,
        )

    def _run_deterministic_validators(self, course_package: CoursePackage) -> list[AuditFinding]:
        findings: list[AuditFinding] = []

        for validator in self._validators:
            findings.extend(validator(course_package))

        return findings

    def _run_semantic_audit(self, course_package: CoursePackage) -> list[AuditFinding]:
        request = build_complete_semantic_audit_request(course_package)

        result = self._coordinator.invoke({"messages": [{"role": "user", "content": request}]})
        structured_response = result.get("structured_response")

        if structured_response is None:
            raise RuntimeError("The audit coordinator did not return a structured response.")

        agent_result = AgentAuditResult.model_validate(structured_response)
        return agent_result.findings

    @staticmethod
    def _determine_status(findings: list[AuditFinding]) -> AuditStatus:
        for finding in findings:
            if finding.severity == FindingSeverity.CRITICAL:
                return AuditStatus.NOT_READY

        for finding in findings:
            if finding.severity == FindingSeverity.WARNING:
                return AuditStatus.NEEDS_REVIEW

        return AuditStatus.READY