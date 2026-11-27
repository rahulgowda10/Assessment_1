"""Unit tests for core/grade_service.py business logic and calculations."""

import tempfile
from pathlib import Path
import unittest

import config
from core import grade_service
from core.grade_service import GradebookError
from core.validators import ValidationError
from database import schema


class TestGradeService(unittest.TestCase):
    """Test business rules, grade boundaries, summaries, and error handling."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_gradebook.db"
        schema.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_calculate_grade_boundaries(self):
        self.assertEqual(grade_service.calculate_grade(100.0), "A+")
        self.assertEqual(grade_service.calculate_grade(90.0), "A+")
        self.assertEqual(grade_service.calculate_grade(89.99), "A")
        self.assertEqual(grade_service.calculate_grade(80.0), "A")
        self.assertEqual(grade_service.calculate_grade(79.99), "B")
        self.assertEqual(grade_service.calculate_grade(70.0), "B")
        self.assertEqual(grade_service.calculate_grade(69.99), "C")
        self.assertEqual(grade_service.calculate_grade(60.0), "C")
        self.assertEqual(grade_service.calculate_grade(59.99), "D")
        self.assertEqual(grade_service.calculate_grade(50.0), "D")
        self.assertEqual(grade_service.calculate_grade(49.99), "F")
        self.assertEqual(grade_service.calculate_grade(0.0), "F")

    def test_register_student_success(self):
        student = grade_service.register_student("S101", "Alice", "CS-1", self.db_path)
        self.assertEqual(student["student_id"], "S101")
        self.assertEqual(student["name"], "Alice")
        self.assertEqual(student["class_section"], "CS-1")

    def test_register_duplicate_student_raises_gradebook_error(self):
        grade_service.register_student("S101", "Alice", "CS-1", self.db_path)
        with self.assertRaises(GradebookError) as ctx:
            grade_service.register_student("S101", "Alice Duplicate", "CS-2", self.db_path)
        self.assertIn("already registered", str(ctx.exception))

    def test_register_invalid_data_raises_validation_error(self):
        with self.assertRaises(ValidationError):
            grade_service.register_student("", "Alice", "CS-1", self.db_path)
        with self.assertRaises(ValidationError):
            grade_service.register_student("S101", "   ", "CS-1", self.db_path)
        with self.assertRaises(ValidationError):
            grade_service.register_student("S101", "Alice", "", self.db_path)

    def test_update_student_success(self):
        grade_service.register_student("S101", "Alice", "CS-1", self.db_path)
        updated = grade_service.update_student("S101", name="Alice Smith", class_section="CS-2", db_path=self.db_path)
        self.assertEqual(updated["name"], "Alice Smith")
        self.assertEqual(updated["class_section"], "CS-2")

    def test_update_student_not_found(self):
        with self.assertRaises(GradebookError) as ctx:
            grade_service.update_student("S999", name="Nobody", db_path=self.db_path)
        self.assertIn("not found", str(ctx.exception))

    def test_remove_student_success_and_not_found(self):
        grade_service.register_student("S101", "Alice", "CS-1", self.db_path)
        grade_service.remove_student("S101", self.db_path)
        # Should now be gone
        with self.assertRaises(GradebookError):
            grade_service.get_student_result("S101", self.db_path)

        # Deleting again raises not found
        with self.assertRaises(GradebookError):
            grade_service.remove_student("S101", self.db_path)

    def test_record_marks_and_get_student_result(self):
        grade_service.register_student("S101", "Alice", "CS-1", self.db_path)

        marks = {
            "Python": 92.0,
            "Database": 88.0,
            "Computer Networks": 78.0,
            "Web Technology": 82.0,
        }
        res = grade_service.record_marks("S101", marks, self.db_path)
        self.assertTrue(res["complete"])
        self.assertEqual(res["missing_subjects"], [])
        self.assertEqual(res["total"], 340.0)
        self.assertEqual(res["average"], 85.0)
        self.assertEqual(res["percentage"], 85.0)
        self.assertEqual(res["grade"], "A")

    def test_incomplete_marks_stay_none_and_never_zero(self):
        grade_service.register_student("S101", "Alice", "CS-1", self.db_path)
        # Only record Python mark
        grade_service.record_mark("S101", "Python", 90.0, self.db_path)

        res = grade_service.get_student_result("S101", self.db_path)
        self.assertFalse(res["complete"])
        self.assertIn("Database", res["missing_subjects"])
        self.assertIn("Computer Networks", res["missing_subjects"])
        self.assertIn("Web Technology", res["missing_subjects"])
        self.assertIsNone(res["total"])
        self.assertIsNone(res["average"])
        self.assertIsNone(res["percentage"])
        self.assertIsNone(res["grade"])

    def test_performance_summary_empty(self):
        summary = grade_service.get_performance_summary(self.db_path)
        self.assertEqual(summary["student_count"], 0)
        self.assertEqual(summary["graded_count"], 0)
        self.assertEqual(summary["incomplete_count"], 0)
        self.assertIsNone(summary["class_average"])
        self.assertIsNone(summary["highest"])
        self.assertIsNone(summary["lowest"])

    def test_performance_summary_with_known_records(self):
        # Register 3 students:
        # S1: Alice -> 95, 95, 95, 95 = Total 380, 95% -> A+
        # S2: Bob -> 70, 70, 70, 70 = Total 280, 70% -> B
        # S3: Charlie -> 40, 40, 40, 40 = Total 160, 40% -> F
        # S4: Dave -> Incomplete (only 1 subject)
        grade_service.register_student("S1", "Alice", "CS", self.db_path)
        grade_service.register_student("S2", "Bob", "CS", self.db_path)
        grade_service.register_student("S3", "Charlie", "CS", self.db_path)
        grade_service.register_student("S4", "Dave", "CS", self.db_path)

        grade_service.record_marks("S1", {s: 95.0 for s in config.SUBJECTS}, self.db_path)
        grade_service.record_marks("S2", {s: 70.0 for s in config.SUBJECTS}, self.db_path)
        grade_service.record_marks("S3", {s: 40.0 for s in config.SUBJECTS}, self.db_path)
        grade_service.record_marks("S4", {"Python": 50.0}, self.db_path)

        summary = grade_service.get_performance_summary(self.db_path)
        self.assertEqual(summary["student_count"], 4)
        self.assertEqual(summary["graded_count"], 3)
        self.assertEqual(summary["incomplete_count"], 1)

        # Average of 95, 70, 40 = 205 / 3 = 68.33
        self.assertEqual(summary["class_average"], 68.33)

        # Highest performer
        self.assertEqual(summary["highest"]["student_id"], "S1")
        self.assertEqual(summary["highest"]["percentage"], 95.0)
        self.assertEqual(summary["highest"]["grade"], "A+")

        # Lowest performer
        self.assertEqual(summary["lowest"]["student_id"], "S3")
        self.assertEqual(summary["lowest"]["percentage"], 40.0)
        self.assertEqual(summary["lowest"]["grade"], "F")

        # Distribution
        self.assertEqual(summary["grade_distribution"]["A+"], 1)
        self.assertEqual(summary["grade_distribution"]["A"], 0)
        self.assertEqual(summary["grade_distribution"]["B"], 1)
        self.assertEqual(summary["grade_distribution"]["C"], 0)
        self.assertEqual(summary["grade_distribution"]["D"], 0)
        self.assertEqual(summary["grade_distribution"]["F"], 1)


if __name__ == "__main__":
    unittest.main()
