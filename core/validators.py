"""Input validation shared by the CLI and the PySide6 GUI.

Every validator either returns a clean, normalised value or raises
``ValidationError``. The interfaces only have to display the message; they
never re-implement a rule.
"""

import math

from config import MAX_MARK_PER_SUBJECT, SUBJECTS


class ValidationError(Exception):
    """Raised when user-supplied data breaks a gradebook business rule."""


def validate_student_id(raw):
    """Return a trimmed, non-empty student ID."""
    value = "" if raw is None else str(raw).strip()
    if not value:
        raise ValidationError("Student ID is required.")
    return value


def validate_name(raw):
    """Return a trimmed student name that is not blank."""
    value = "" if raw is None else str(raw).strip()
    if not value:
        raise ValidationError("Student name is required.")
    return value


def validate_class_section(raw):
    """Return a trimmed class/section that is not blank."""
    value = "" if raw is None else str(raw).strip()
    if not value:
        raise ValidationError("Class/section is required.")
    return value


def validate_subject(subject):
    """Return the subject name if it belongs to the configured subject list."""
    value = "" if subject is None else str(subject).strip()
    if value not in SUBJECTS:
        raise ValidationError(
            f"Unknown subject '{value}'. Valid subjects: {', '.join(SUBJECTS)}."
        )
    return value


def validate_mark(raw):
    """Return a mark as a float between 0 and 100 inclusive.

    Accepts numbers or numeric strings. Booleans, blanks, text and
    out-of-range values are rejected with a readable message.
    """
    if isinstance(raw, bool):
        raise ValidationError("Mark must be a number between 0 and 100.")

    if isinstance(raw, (int, float)):
        value = float(raw)
    else:
        text = "" if raw is None else str(raw).strip()
        if not text:
            raise ValidationError("Mark is required and must be a number.")
        try:
            value = float(text)
        except ValueError:
            raise ValidationError(
                f"Mark must be a number, got '{text}'."
            ) from None

    if not math.isfinite(value):
        raise ValidationError("Mark must be a finite number between 0 and 100.")
    if value < 0 or value > MAX_MARK_PER_SUBJECT:
        raise ValidationError(
            f"Mark must be between 0 and {MAX_MARK_PER_SUBJECT:g}, got {value:g}."
        )
    return value
