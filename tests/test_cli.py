"""Unit tests for main_cli.py menu interactions, I/O handling, and commands."""

import tempfile
from pathlib import Path
import unittest

from database import connection, schema
import main_cli


class FakeIO:
    """Helper to simulate user keyboard inputs and capture CLI print statements."""

    def __init__(self, inputs):
        self._inputs = list(inputs)
        self.outputs = []

    def input(self, prompt=""):
        if not self._inputs:
            raise EOFError("No more simulated inputs.")
        val = self._inputs.pop(0)
        return val

    def print(self, *args, **kwargs):
        self.outputs.append(" ".join(str(a) for a in args))


class TestCLI(unittest.TestCase):
    """Test CLI commands and menu options using injected fake I/O."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_gradebook.db"
        connection.set_database_path(self.db_path)
        schema.initialize_database(self.db_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_cli_add_student_and_view_all(self):
        # 1: Add student (S101, Alice, CS1)
        # 3: View all students
        # 9: Exit
        io = FakeIO([
            "1", "S101", "Alice", "CS1",
            "3",
            "9"
        ])
        exit_code = main_cli.run(input_fn=io.input, print_fn=io.print)
        self.assertEqual(exit_code, 0)

        output_text = "\n".join(io.outputs)
        self.assertIn("Student 'Alice' (S101) added.", output_text)
        self.assertIn("S101", output_text)
        self.assertIn("Alice", output_text)
        self.assertIn("Total students: 1", output_text)

    def test_cli_enter_marks_and_view_result(self):
        # 1: Add student
        # 2: Enter marks (Python: 80, Database: 85, Networks: 90, Web: 95)
        # 5: View result
        # 9: Exit
        io = FakeIO([
            "1", "S202", "Bob", "CS2",
            "2", "S202", "80", "85", "90", "95",
            "5", "S202",
            "9"
        ])
        exit_code = main_cli.run(input_fn=io.input, print_fn=io.print)
        self.assertEqual(exit_code, 0)

        output_text = "\n".join(io.outputs)
        self.assertIn("Marks saved for Bob.", output_text)
        self.assertIn("Total", output_text)
        self.assertIn("350", output_text)
        self.assertIn("Average", output_text)
        self.assertIn("87.50", output_text)
        self.assertIn("Percentage", output_text)
        self.assertIn("87.50%", output_text)
        self.assertIn("Grade", output_text)
        self.assertIn("A", output_text)

    def test_cli_search_and_update_student(self):
        # 1: Add student S303, Charlie, CS3
        # 4: Search "Char"
        # 7: Update student S303 (New Name: "Charles", Class: "")
        # 4: Search "Charles"
        # 9: Exit
        io = FakeIO([
            "1", "S303", "Charlie", "CS3",
            "4", "Char",
            "7", "S303", "Charles", "",
            "4", "Charles",
            "9"
        ])
        main_cli.run(input_fn=io.input, print_fn=io.print)
        output_text = "\n".join(io.outputs)
        self.assertIn("Charlie", output_text)
        self.assertIn("Updated student S303: Charles / CS3", output_text)

    def test_cli_delete_student_confirmed(self):
        # 1: Add student
        # 8: Delete student (confirm 'y')
        # 3: View all (empty)
        # 9: Exit
        io = FakeIO([
            "1", "S404", "David", "CS4",
            "8", "S404", "y",
            "3",
            "9"
        ])
        main_cli.run(input_fn=io.input, print_fn=io.print)
        output_text = "\n".join(io.outputs)
        self.assertIn("Student 'S404' deleted.", output_text)
        self.assertIn("No students registered yet.", output_text)

    def test_cli_delete_student_cancelled(self):
        io = FakeIO([
            "1", "S405", "Emma", "CS4",
            "8", "S405", "n",
            "3",
            "9"
        ])
        main_cli.run(input_fn=io.input, print_fn=io.print)
        output_text = "\n".join(io.outputs)
        self.assertIn("Deletion cancelled.", output_text)
        self.assertIn("Emma", output_text)

    def test_cli_view_summary(self):
        # Add two students with complete marks, view summary
        io = FakeIO([
            "1", "S1", "Alice", "CS",
            "2", "S1", "90", "90", "90", "90",
            "1", "S2", "Bob", "CS",
            "2", "S2", "60", "60", "60", "60",
            "6",
            "9"
        ])
        main_cli.run(input_fn=io.input, print_fn=io.print)
        output_text = "\n".join(io.outputs)
        self.assertIn("CLASS PERFORMANCE SUMMARY", output_text)
        self.assertIn("Students: 2", output_text)
        self.assertIn("Complete results: 2", output_text)
        self.assertIn("Class average: 75.00%", output_text)
        self.assertIn("Highest: Alice (S1) - 90.00% [A+]", output_text)
        self.assertIn("Lowest: Bob (S2) - 60.00% [C]", output_text)

    def test_cli_error_handling_does_not_crash(self):
        # Invalid choice, then duplicate student ID, then invalid mark, then exit
        io = FakeIO([
            "99",  # invalid choice
            "1", "S1", "First", "CS",
            "1", "S1", "Duplicate", "CS",  # duplicate ID error
            "2", "S1", "invalid_mark", "", "", "",  # invalid mark error
            "9"
        ])
        exit_code = main_cli.run(input_fn=io.input, print_fn=io.print)
        self.assertEqual(exit_code, 0)
        output_text = "\n".join(io.outputs)
        self.assertIn("Invalid choice. Enter a number from 1 to 9.", output_text)
        self.assertIn("Error: Student ID 'S1' is already registered.", output_text)
        self.assertIn("Error: Mark must be a number, got 'invalid_mark'.", output_text)


if __name__ == "__main__":
    unittest.main()
