from datetime import datetime
import json
from pathlib import Path
from .domain.models import AssessmentRecord, CourseDocument, CoursePackage, CourseTopic

# This class is ONLY used to load a course package from a given path & return a CoursePackage object.
# It does not perform any auditing or analysis.
class CoursePackageLoader:
    def load_course_package(self, course_package_path: Path) -> CoursePackage:
        course_documents = self._load_course_documents(course_package_path)
        course_name, topics, schedule_assessments = self._load_schedule(course_package_path / "course_schedule.json")
        syllabus_assessments = self._load_syllabus(course_package_path / "syllabus.md")

        return CoursePackage(
            course_name=course_name,
            topics=topics,
            assessments=[
                *syllabus_assessments,
                *schedule_assessments,
            ],
            documents=course_documents,
        )

    # Returns a tuple of (course_name, list of CourseTopic, list of AssessmentRecord)
    def _load_schedule(self, schedule_path: Path) -> tuple[str, list[CourseTopic], list[AssessmentRecord]]:
        with schedule_path.open(encoding="utf-8") as f:
            data = json.load(f)
            course_name = data["course_name"]
            topics = [
                CourseTopic(
                    id=topic["id"],
                    name=topic["name"],
                    teaching_date=datetime.strptime(topic["teaching_date"], "%Y-%m-%d").date()
                )
                for topic in data.get("topics", [])
            ]
            assessments = [
                AssessmentRecord(
                    id=assessment["id"],
                    name=assessment["name"],
                    source_file=schedule_path.name,
                    due_date=datetime.strptime(assessment["due_date"], "%Y-%m-%d").date() if assessment.get("due_date") else None,
                    required_topic_ids=assessment.get("required_topic_ids", [])
                )
                for assessment in data["assessments"]
            ]
        return course_name, topics, assessments

    # Returns a list of AssessmentRecord objects loaded from the syllabus
    # All other info is only relevant for audit/analysis. 
    def _load_syllabus(self, syllabus_path: Path) -> list[AssessmentRecord]:
        content = syllabus_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        table_header = ("| ID | Assessment | Weight | Due Date | Required Topic IDs |")
        header_index = lines.index(table_header)

        # Skip the header and Markdown separator rows.
        assessment_lines = []

        for line in lines[header_index + 2 :]:
            if not line.strip().startswith("|"):
                break

            assessment_lines.append(line)

        assessments = []

        for line in assessment_lines:
            (assessment_id, name, weight_text, due_date_text, required_topics_text) = self._parse_markdown_row(line)

            assessments.append(
                AssessmentRecord(
                    id=assessment_id,
                    name=name,
                    source_file=syllabus_path.name,
                    weight=(
                        float(weight_text.removesuffix("%"))
                        if weight_text
                        else None
                    ),
                    due_date=(
                        datetime.strptime(due_date_text, "%Y-%m-%d").date()
                        if due_date_text
                        else None
                    ),
                    required_topic_ids=[
                        topic.strip()
                        for topic in required_topics_text.split(",")
                        if topic.strip()
                    ],
                )
            )
        return assessments

    # Loads & returns a list of CourseDocument objects
    # ONLY WORKS for the 4 expected documents (syllabus, course schedule, assignment brief, grading rubric)
    def _load_course_documents(self, documents_path: Path) -> list[CourseDocument]:
        documents = [
            CourseDocument(source_file=path.name, content=path.read_text(encoding="utf-8"))
            for path in [
                documents_path / "syllabus.md",
                documents_path / "course_schedule.json",
                documents_path / "assignment_brief.md",
                documents_path / "grading_rubric.md",
            ]
        ]
        return documents

    # Example input: "| assignment-1 | API Design Proposal | 20% | 2026-09-30 | api-design |"
    # Example output: ["assignment-1", "API Design Proposal", "20%", "2026-09-30", "api-design"]
    @staticmethod
    def _parse_markdown_row(line: str) -> list[str]:
        return [
            cell.strip()
            for cell in line.strip().strip("|").split("|")
        ]