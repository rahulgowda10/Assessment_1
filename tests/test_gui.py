"""Unit tests for PySide6 GUI (gui/main_window.py) and CLI-GUI feature parity."""

import sys
import tempfile
from pathlib import Path
import unittest

from PySide6.QtWidgets import QApplication

import config
from core import grade_service
from database import connection, schema
from gui.main_window import MainWindow

# Ensure single QApplication instance across test runner
app = QApplication.instance() or QApplication(sys.argv)


class TestGUI(unittest.TestCase):
    """Test PySide6 GUI components, event handlers, and calculations."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_gradebook.db"
        connection.set_database_path(self.db_path)
        schema.initialize_database(self.db_path)
        self.window = MainWindow()
        # Mock dialogs so unit tests don't block
        self.window.show_info = lambda title, msg: None
        self.window.show_error = lambda msg: None

    def tearDown(self):
        self.window.close()
        self.temp_dir.cleanup()

    def test_gui_add_student(self):
        self.window._add_id_input.setText("S101")
        self.window._add_name_input.setText("Alice Smith")
        self.window._add_class_input.setText("Year 1")
        self.window._on_add_student()

        # Check student appears in table
        self.assertEqual(self.window._student_table.rowCount(), 1)
        self.assertEqual(self.window._student_table.item(0, 0).text(), "S101")
        self.assertEqual(self.window._student_table.item(0, 1).text(), "Alice Smith")
        self.assertEqual(self.window._student_table.item(0, 2).text(), "Year 1")

    def test_gui_search_students(self):
        grade_service.register_student("S101", "Alice", "CS-A", self.db_path)
        grade_service.register_student("S102", "Bob", "CS-B", self.db_path)
        self.window.refresh_all()

        # Search for Alice
        self.window._student_search_input.setText("Alice")
        self.window._on_search_students()
        self.assertEqual(self.window._student_table.rowCount(), 1)
        self.assertEqual(self.window._student_table.item(0, 1).text(), "Alice")

        # Clear search
        self.window._on_clear_search()
        self.assertEqual(self.window._student_table.rowCount(), 2)

    def test_gui_update_student(self):
        grade_service.register_student("S101", "Alice", "CS-A", self.db_path)
        self.window.refresh_all()

        # Select student row
        self.window._student_table.selectRow(0)
        self.assertEqual(self.window._edit_id_label.text(), "S101")

        # Update details
        self.window._edit_name_input.setText("Alice Cooper")
        self.window._edit_class_input.setText("CS-Advanced")
        self.window._on_update_student()

        student = grade_service.list_students(self.db_path)[0]
        self.assertEqual(student["name"], "Alice Cooper")
        self.assertEqual(student["class_section"], "CS-Advanced")

    def test_gui_delete_student(self):
        grade_service.register_student("S101", "Alice", "CS-A", self.db_path)
        self.window.refresh_all()

        from PySide6.QtWidgets import QMessageBox
        original_question = QMessageBox.question
        QMessageBox.question = lambda *args, **kwargs: QMessageBox.Yes
        try:
            self.window._student_table.selectRow(0)
            self.window._on_delete_student()
            self.assertEqual(len(grade_service.list_students(self.db_path)), 0)
        finally:
            QMessageBox.question = original_question

    def test_gui_save_marks_and_view_result(self):
        grade_service.register_student("S101", "Alice", "CS-A", self.db_path)
        self.window.refresh_all()

        # Select student in marks combo (index 1 is the registered student)
        self.window._marks_student_combo.setCurrentIndex(1)
        self.assertEqual(self.window._marks_student_combo.currentData(), "S101")

        # Fill marks
        for subject in config.SUBJECTS:
            self.window._mark_inputs[subject].setText("85")

        self.window._on_save_marks()

        # Verify result in service and on result tab
        res = grade_service.get_student_result("S101", self.db_path)
        self.assertTrue(res["complete"])
        self.assertEqual(res["total"], 340.0)
        self.assertEqual(res["average"], 85.0)
        self.assertEqual(res["percentage"], 85.0)
        self.assertEqual(res["grade"], "A")

        # Verify Result tab display
        self.window._result_student_combo.setCurrentIndex(1)
        self.assertEqual(self.window._res_total_label.text(), "340 / 400")
        self.assertEqual(self.window._res_avg_label.text(), "85.00")
        self.assertEqual(self.window._res_pct_label.text(), "85.00%")
        self.assertEqual(self.window._res_grade_label.text(), "A")
        self.assertIn("COMPLETE", self.window._res_status_label.text())

    def test_gui_dashboard_and_summary_display(self):
        grade_service.register_student("S1", "High Student", "CS", self.db_path)
        grade_service.register_student("S2", "Low Student", "CS", self.db_path)
        grade_service.register_student("S3", "Incomplete Student", "CS", self.db_path)

        grade_service.record_marks("S1", {s: 90.0 for s in config.SUBJECTS}, self.db_path)
        grade_service.record_marks("S2", {s: 60.0 for s in config.SUBJECTS}, self.db_path)

        self.window.refresh_all()

        # Dashboard labels
        self.assertEqual(self.window._dash_total_label[1].text(), "3")
        self.assertEqual(self.window._dash_graded_label[1].text(), "2")
        self.assertEqual(self.window._dash_incomplete_label[1].text(), "1")
        self.assertEqual(self.window._dash_avg_label[1].text(), "75.00%")
        self.assertIn("High Student", self.window._dash_highest_label.text())
        self.assertIn("Low Student", self.window._dash_lowest_label.text())

        # Class Summary Tab
        self.assertEqual(self.window._sum_table.rowCount(), 3)

    def test_cli_gui_feature_parity(self):
        """Verify that CLI and GUI share identical calculations, rules, and outcomes."""
        # 1. Register student through service
        grade_service.register_student("S parity", "Parity User", "CS-Parity", self.db_path)

        # 2. Enter incomplete marks
        grade_service.record_mark("S parity", "Python", 90.0, self.db_path)
        service_res = grade_service.get_student_result("S parity", self.db_path)

        # Both agree result is incomplete and missing marks are not zero
        self.assertFalse(service_res["complete"])
        self.assertIsNone(service_res["total"])
        self.assertIsNone(service_res["grade"])

        # 3. Enter remaining marks
        grade_service.record_marks(
            "S parity",
            {"Database": 80.0, "Computer Networks": 85.0, "Web Technology": 75.0},
            self.db_path,
        )
        completed_res = grade_service.get_student_result("S parity", self.db_path)

        # Total = 90 + 80 + 85 + 75 = 330. Avg = 82.5, Pct = 82.5%, Grade = A
        self.assertEqual(completed_res["total"], 330.0)
        self.assertEqual(completed_res["average"], 82.5)
        self.assertEqual(completed_res["percentage"], 82.5)
        self.assertEqual(completed_res["grade"], "A")

        # Now load in GUI and assert parity
        self.window.refresh_all()
        self.window._result_student_combo.setCurrentIndex(1)
        self.assertEqual(self.window._res_total_label.text(), "330 / 400")
        self.assertEqual(self.window._res_avg_label.text(), "82.50")
        self.assertEqual(self.window._res_pct_label.text(), "82.50%")
        self.assertEqual(self.window._res_grade_label.text(), "A")


if __name__ == "__main__":
    unittest.main()
