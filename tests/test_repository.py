"""Unit tests for database/student_repository.py, connection.py, and schema.py."""

import sqlite3
import tempfile
from pathlib import Path
import unittest

from database import connection, schema, student_repository as repo


class TestRepository(unittest.TestCase):
    """Test SQLite database operations, schema constraints, and repository methods."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_gradebook.db"
        schema.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_schema_tables_exist(self):
        with connection.connection_scope(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row["name"] for row in cursor.fetchall()]
        self.assertIn("students", tables)
        self.assertIn("marks", tables)

    def test_add_and_get_student(self):
        repo.add_student("S100", "Charlie Brown", "CS-101", self.db_path)
        student = repo.get_student("S100", self.db_path)
        self.assertIsNotNone(student)
        self.assertEqual(student["student_id"], "S100")
        self.assertEqual(student["name"], "Charlie Brown")
        self.assertEqual(student["class_section"], "CS-101")
        self.assertIn("created_at", student)

    def test_duplicate_student_id_raises_integrity_error(self):
        repo.add_student("S100", "Charlie Brown", "CS-101", self.db_path)
        with self.assertRaises(sqlite3.IntegrityError):
            repo.add_student("S100", "Duplicate Charlie", "CS-102", self.db_path)

    def test_get_all_students(self):
        repo.add_student("S200", "Bob", "CS-A", self.db_path)
        repo.add_student("S100", "Alice", "CS-A", self.db_path)
        students = repo.get_all_students(self.db_path)
        self.assertEqual(len(students), 2)
        # Should be ordered by student_id
        self.assertEqual(students[0]["student_id"], "S100")
        self.assertEqual(students[1]["student_id"], "S200")

    def test_search_students(self):
        repo.add_student("S101", "Alice Wonder", "CS-A", self.db_path)
        repo.add_student("S102", "Bob Marley", "CS-B", self.db_path)
        repo.add_student("S201", "Charlie Alice", "CS-A", self.db_path)

        # Search by name fragment
        results = repo.search_students("Alice", self.db_path)
        self.assertEqual(len(results), 2)
        ids = [r["student_id"] for r in results]
        self.assertIn("S101", ids)
        self.assertIn("S201", ids)

        # Search by ID fragment
        results = repo.search_students("201", self.db_path)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["student_id"], "S201")

        # No match
        results = repo.search_students("Nonexistent", self.db_path)
        self.assertEqual(len(results), 0)

    def test_update_student(self):
        repo.add_student("S100", "Old Name", "Old Class", self.db_path)
        rows_changed = repo.update_student("S100", "New Name", "New Class", self.db_path)
        self.assertEqual(rows_changed, 1)

        student = repo.get_student("S100", self.db_path)
        self.assertEqual(student["name"], "New Name")
        self.assertEqual(student["class_section"], "New Class")

    def test_save_marks_and_update_marks(self):
        repo.add_student("S100", "Alice", "CS-A", self.db_path)

        # Insert marks
        repo.save_marks("S100", {"Python": 85.0, "Database": 90.0}, self.db_path)
        marks = repo.get_marks("S100", self.db_path)
        self.assertEqual(marks["Python"], 85.0)
        self.assertEqual(marks["Database"], 90.0)

        # Update marks for the same student and subject (UPSERT)
        repo.save_marks("S100", {"Python": 95.0}, self.db_path)
        marks_updated = repo.get_marks("S100", self.db_path)
        self.assertEqual(marks_updated["Python"], 95.0)
        self.assertEqual(marks_updated["Database"], 90.0)

    def test_get_student_with_marks(self):
        repo.add_student("S100", "Alice", "CS-A", self.db_path)
        repo.save_marks("S100", {"Python": 88.0}, self.db_path)

        res = repo.get_student_with_marks("S100", self.db_path)
        self.assertEqual(res["student_id"], "S100")
        self.assertEqual(res["marks"], {"Python": 88.0})

        self.assertIsNone(repo.get_student_with_marks("S999", self.db_path))

    def test_foreign_key_cascade_deletion(self):
        """Deleting a student must automatically delete associated marks via ON DELETE CASCADE."""
        repo.add_student("S100", "Alice", "CS-A", self.db_path)
        repo.save_marks("S100", {"Python": 90.0, "Database": 85.0}, self.db_path)

        # Confirm marks exist
        self.assertEqual(len(repo.get_marks("S100", self.db_path)), 2)

        # Delete student
        repo.delete_student("S100", self.db_path)
        self.assertIsNone(repo.get_student("S100", self.db_path))

        # Check marks table directly
        with connection.connection_scope(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM marks WHERE student_id = ?", ("S100",))
            remaining_marks = cursor.fetchall()
        self.assertEqual(len(remaining_marks), 0, "Marks should be deleted via cascade.")

    def test_data_persistence(self):
        """Data must persist across independent connection sessions."""
        repo.add_student("S300", "Persistent Paul", "CS-X", self.db_path)
        repo.save_marks("S300", {"Python": 77.0}, self.db_path)

        # Create brand new connection to the same SQLite file
        new_conn = connection.get_connection(self.db_path)
        row = new_conn.execute("SELECT name FROM students WHERE student_id = ?", ("S300",)).fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row["name"], "Persistent Paul")

        mark_row = new_conn.execute(
            "SELECT mark FROM marks WHERE student_id = ? AND subject = ?", ("S300", "Python")
        ).fetchone()
        self.assertIsNotNone(mark_row)
        self.assertEqual(mark_row["mark"], 77.0)
        new_conn.close()


if __name__ == "__main__":
    unittest.main()
