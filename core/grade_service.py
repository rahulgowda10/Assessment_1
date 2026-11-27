"""Gradebook business logic shared by the CLI and the GUI.

The interfaces call these functions; they never calculate a grade, validate a
mark or run SQL themselves.
"""

import sqlite3

from config import GRADE_SCALE, MAX_TOTAL_MARKS, SUBJECTS
from core import validators
from core.validators import ValidationError
from database import student_repository as repository


class GradebookError(Exception):
    """A business-rule or lookup error that can be shown to the user."""


def calculate_grade(percentage):
    """Return the letter grade for a percentage using config.GRADE_SCALE."""
    for minimum, grade in GRADE_SCALE:
        if percentage >= minimum:
            return grade
    return "F"


def build_result(student):
    """Turn a student row (with 'marks') into a full result dictionary.

    When any subject is missing the result is marked incomplete and total,
    average, percentage and grade stay None. Missing marks are never zero.
    """
    marks = student["marks"]
    missing = [subject for subject in SUBJECTS if subject not in marks]
    result = {
        "student_id": student["student_id"],
        "name": student["name"],
        "class_section": student["class_section"],
        "marks": {subject: marks.get(subject) for subject in SUBJECTS},
        "missing_subjects": missing,
        "complete": not missing,
        "total": None,
        "average": None,
        "percentage": None,
        "grade": None,
    }
    if missing:
        return result

    total = sum(marks[subject] for subject in SUBJECTS)
    percentage = total / MAX_TOTAL_MARKS * 100
    result["total"] = round(total, 2)
    result["average"] = round(total / len(SUBJECTS), 2)
    result["percentage"] = round(percentage, 2)
    result["grade"] = calculate_grade(percentage)
    return result


def register_student(student_id, name, class_section, db_path=None):
    """Validate and save a new student, rejecting duplicate IDs."""
    student_id = validators.validate_student_id(student_id)
    name = validators.validate_name(name)
    class_section = validators.validate_class_section(class_section)
    try:
        return repository.add_student(student_id, name, class_section, db_path)
    except sqlite3.IntegrityError:
        raise GradebookError(
            f"Student ID '{student_id}' is already registered."
        ) from None


def update_student(student_id, name=None, class_section=None, db_path=None):
    """Update the name and/or class/section of an existing student."""
    student_id = validators.validate_student_id(student_id)
    if name is None and class_section is None:
        raise GradebookError("Provide a new name or class/section to update.")

    student = repository.get_student(student_id, db_path)
    if student is None:
        raise GradebookError(f"Student '{student_id}' was not found.")

    new_name = student["name"] if name is None else validators.validate_name(name)
    new_class = (
        student["class_section"]
        if class_section is None
        else validators.validate_class_section(class_section)
    )
    repository.update_student(student_id, new_name, new_class, db_path)
    return repository.get_student(student_id, db_path)


def remove_student(student_id, db_path=None):
    """Delete a student and, through the cascade, all of their marks."""
    student_id = validators.validate_student_id(student_id)
    if repository.get_student(student_id, db_path) is None:
        raise GradebookError(f"Student '{student_id}' was not found.")
    repository.delete_student(student_id, db_path)


def record_mark(student_id, subject, mark, db_path=None):
    """Validate and save one subject mark (add or update)."""
    return record_marks(student_id, {subject: mark}, db_path)


def record_marks(student_id, marks, db_path=None):
    """Validate and save several subject marks in one transaction."""
    student_id = validators.validate_student_id(student_id)
    if not marks:
        raise GradebookError("No marks were provided.")
    if repository.get_student(student_id, db_path) is None:
        raise GradebookError(f"Student '{student_id}' was not found.")

    clean_marks = {}
    for subject, mark in marks.items():
        clean_marks[validators.validate_subject(subject)] = (
            validators.validate_mark(mark)
        )

    repository.save_marks(student_id, clean_marks, db_path)
    return get_student_result(student_id, db_path)


def get_student_result(student_id, db_path=None):
    """Return the calculated result for one student."""
    student_id = validators.validate_student_id(student_id)
    student = repository.get_student_with_marks(student_id, db_path)
    if student is None:
        raise GradebookError(f"Student '{student_id}' was not found.")
    return build_result(student)


def _results_for(students, db_path=None):
    """Build result dictionaries for a list of student rows."""
    results = []
    for student in students:
        student["marks"] = repository.get_marks(student["student_id"], db_path)
        results.append(build_result(student))
    return results


def list_students(db_path=None):
    """Return every student row."""
    return repository.get_all_students(db_path)


def get_all_student_results(db_path=None):
    """Return calculated results for every student."""
    return _results_for(repository.get_all_students(db_path), db_path)


def search_students(keyword, db_path=None):
    """Return student results matching an ID or name fragment."""
    keyword = "" if keyword is None else str(keyword).strip()
    if not keyword:
        return get_all_student_results(db_path)
    return _results_for(repository.search_students(keyword, db_path), db_path)


def get_performance_summary(db_path=None):
    """Return class-level statistics based only on complete results.

    Ties are broken by student ID so the output is always deterministic.
    """
    results = get_all_student_results(db_path)
    complete = [result for result in results if result["complete"]]
    summary = {
        "student_count": len(results),
        "graded_count": len(complete),
        "incomplete_count": len(results) - len(complete),
        "class_average": None,
        "highest": None,
        "lowest": None,
        "grade_distribution": {grade: 0 for _, grade in GRADE_SCALE},
    }
    if not complete:
        return summary

    summary["class_average"] = round(
        sum(result["percentage"] for result in complete) / len(complete), 2
    )
    ranked = sorted(complete, key=lambda item: (item["percentage"], item["student_id"]))
    summary["lowest"] = ranked[0]
    summary["highest"] = ranked[-1]
    for result in complete:
        summary["grade_distribution"][result["grade"]] += 1
    return summary
