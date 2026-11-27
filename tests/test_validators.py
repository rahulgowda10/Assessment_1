"""Unit tests for core/validators.py."""

import unittest
from core.validators import (
    ValidationError,
    validate_class_section,
    validate_mark,
    validate_name,
    validate_student_id,
    validate_subject,
)


class TestValidators(unittest.TestCase):
    """Test input validation rules for student details and subject marks."""

    def test_validate_student_id_valid(self):
        self.assertEqual(validate_student_id("S101"), "S101")
        self.assertEqual(validate_student_id("  S102  "), "S102")

    def test_validate_student_id_invalid(self):
        with self.assertRaises(ValidationError):
            validate_student_id("")
        with self.assertRaises(ValidationError):
            validate_student_id("   ")
        with self.assertRaises(ValidationError):
            validate_student_id(None)

    def test_validate_name_valid(self):
        self.assertEqual(validate_name("Alice Smith"), "Alice Smith")
        self.assertEqual(validate_name("  Bob  "), "Bob")

    def test_validate_name_invalid(self):
        with self.assertRaises(ValidationError):
            validate_name("")
        with self.assertRaises(ValidationError):
            validate_name("   ")
        with self.assertRaises(ValidationError):
            validate_name(None)

    def test_validate_class_section_valid(self):
        self.assertEqual(validate_class_section("CS-A"), "CS-A")
        self.assertEqual(validate_class_section("  Year 2  "), "Year 2")

    def test_validate_class_section_invalid(self):
        with self.assertRaises(ValidationError):
            validate_class_section("")
        with self.assertRaises(ValidationError):
            validate_class_section("   ")
        with self.assertRaises(ValidationError):
            validate_class_section(None)

    def test_validate_subject_valid(self):
        self.assertEqual(validate_subject("Python"), "Python")
        self.assertEqual(validate_subject("Database"), "Database")
        self.assertEqual(validate_subject("Computer Networks"), "Computer Networks")
        self.assertEqual(validate_subject("Web Technology"), "Web Technology")

    def test_validate_subject_invalid(self):
        with self.assertRaises(ValidationError):
            validate_subject("Biology")
        with self.assertRaises(ValidationError):
            validate_subject("")
        with self.assertRaises(ValidationError):
            validate_subject(None)

    def test_validate_mark_valid(self):
        self.assertEqual(validate_mark(0), 0.0)
        self.assertEqual(validate_mark(100), 100.0)
        self.assertEqual(validate_mark(75.5), 75.5)
        self.assertEqual(validate_mark("85"), 85.0)
        self.assertEqual(validate_mark(" 92.5 "), 92.5)

    def test_validate_mark_out_of_range(self):
        with self.assertRaises(ValidationError):
            validate_mark(-1)
        with self.assertRaises(ValidationError):
            validate_mark(100.1)
        with self.assertRaises(ValidationError):
            validate_mark("-5")
        with self.assertRaises(ValidationError):
            validate_mark("105")

    def test_validate_mark_non_numeric(self):
        with self.assertRaises(ValidationError):
            validate_mark("abc")
        with self.assertRaises(ValidationError):
            validate_mark("")
        with self.assertRaises(ValidationError):
            validate_mark(None)
        with self.assertRaises(ValidationError):
            validate_mark(True)  # boolean should not be accepted as numeric mark
        with self.assertRaises(ValidationError):
            validate_mark(False)
        with self.assertRaises(ValidationError):
            validate_mark(float("nan"))
        with self.assertRaises(ValidationError):
            validate_mark(float("inf"))


if __name__ == "__main__":
    unittest.main()
