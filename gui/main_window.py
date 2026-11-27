from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import config
from core import grade_service
from core.validators import ValidationError


class MainWindow(QMainWindow):
    """Main window containing all gradebook screens in a tabbed interface."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Student Gradebook & Performance Analyzer")
        self.resize(950, 680)

        self._central_widget = QWidget()
        self.setCentralWidget(self._central_widget)
        self._main_layout = QVBoxLayout(self._central_widget)

        self._tabs = QTabWidget()
        self._main_layout.addWidget(self._tabs)

        # Build each screen tab
        self._dashboard_tab = QWidget()
        self._students_tab = QWidget()
        self._marks_tab = QWidget()
        self._results_tab = QWidget()
        self._summary_tab = QWidget()

        self._tabs.addTab(self._dashboard_tab, "Dashboard")
        self._tabs.addTab(self._students_tab, "Students")
        self._tabs.addTab(self._marks_tab, "Marks")
        self._tabs.addTab(self._results_tab, "Result")
        self._tabs.addTab(self._summary_tab, "Class Summary")

        self._setup_dashboard_tab()
        self._setup_students_tab()
        self._setup_marks_tab()
        self._setup_results_tab()
        self._setup_summary_tab()

        self._tabs.currentChanged.connect(self._on_tab_changed)

        # Initial data load
        self.refresh_all()

    # -------------------------------------------------------------------------
    # Notification & Error Helpers
    # -------------------------------------------------------------------------

    def show_error(self, message):
        """Display an error message box to the user."""
        QMessageBox.warning(self, "Gradebook Notice", str(message))

    def show_info(self, title, message):
        """Display an informational message box."""
        QMessageBox.information(self, title, str(message))

    # -------------------------------------------------------------------------
    # TAB 1: Dashboard
    # -------------------------------------------------------------------------

    def _setup_dashboard_tab(self):
        layout = QVBoxLayout(self._dashboard_tab)

        title = QLabel("<h2>Performance Dashboard</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Metric cards
        cards_layout = QHBoxLayout()
        self._dash_total_label = self._create_card("Total Students", "0")
        self._dash_graded_label = self._create_card("Complete Results", "0")
        self._dash_incomplete_label = self._create_card("Incomplete Results", "0")
        self._dash_avg_label = self._create_card("Class Average", "N/A")

        cards_layout.addWidget(self._dash_total_label[0])
        cards_layout.addWidget(self._dash_graded_label[0])
        cards_layout.addWidget(self._dash_incomplete_label[0])
        cards_layout.addWidget(self._dash_avg_label[0])
        layout.addLayout(cards_layout)

        # Highlights: Highest & Lowest Performer
        hl_group = QGroupBox("Class Highlights")
        hl_layout = QHBoxLayout(hl_group)

        self._dash_highest_label = QLabel("Highest: None")
        self._dash_lowest_label = QLabel("Lowest: None")
        self._dash_highest_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #1b5e20;")
        self._dash_lowest_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #b71c1c;")

        hl_layout.addWidget(self._dash_highest_label)
        hl_layout.addWidget(self._dash_lowest_label)
        layout.addWidget(hl_group)

        # Grade distribution table
        dist_group = QGroupBox("Grade Distribution")
        dist_layout = QVBoxLayout(dist_group)
        self._dash_dist_table = QTableWidget(len(config.GRADE_SCALE), 3)
        self._dash_dist_table.setHorizontalHeaderLabels(["Grade", "Percentage Range", "Student Count"])
        self._dash_dist_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._dash_dist_table.setEditTriggers(QTableWidget.NoEditTriggers)
        dist_layout.addWidget(self._dash_dist_table)
        layout.addWidget(dist_group)

        # Refresh button
        refresh_btn = QPushButton("Refresh Dashboard")
        refresh_btn.clicked.connect(self.refresh_dashboard)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

    def _create_card(self, title_text, value_text):
        frame = QFrame()
        frame.setFrameShape(QFrame.StyledPanel)
        frame.setStyleSheet("background-color: #f7f9fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 10px;")
        f_layout = QVBoxLayout(frame)
        title = QLabel(title_text)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #555; font-size: 12px;")
        val = QLabel(value_text)
        val.setAlignment(Qt.AlignCenter)
        val.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a237e;")
        f_layout.addWidget(title)
        f_layout.addWidget(val)
        return frame, val

    def refresh_dashboard(self):
        summary = grade_service.get_performance_summary()
        self._dash_total_label[1].setText(str(summary["student_count"]))
        self._dash_graded_label[1].setText(str(summary["graded_count"]))
        self._dash_incomplete_label[1].setText(str(summary["incomplete_count"]))

        if summary["class_average"] is not None:
            self._dash_avg_label[1].setText(f"{summary['class_average']:.2f}%")
        else:
            self._dash_avg_label[1].setText("N/A")

        if summary["highest"]:
            h = summary["highest"]
            self._dash_highest_label.setText(
                f"🏆 Highest: {h['name']} ({h['student_id']}) — {h['percentage']:.2f}% [{h['grade']}]"
            )
        else:
            self._dash_highest_label.setText("🏆 Highest: None")

        if summary["lowest"]:
            low = summary["lowest"]
            self._dash_lowest_label.setText(
                f"⚠️ Lowest: {low['name']} ({low['student_id']}) — {low['percentage']:.2f}% [{low['grade']}]"
            )
        else:
            self._dash_lowest_label.setText("⚠️ Lowest: None")

        # Update distribution table
        scale_ranges = {
            "A+": "90% - 100%",
            "A": "80% - 89.99%",
            "B": "70% - 79.99%",
            "C": "60% - 69.99%",
            "D": "50% - 59.99%",
            "F": "Below 50%",
        }
        for row, (_, grade) in enumerate(config.GRADE_SCALE):
            count = summary["grade_distribution"].get(grade, 0)
            range_desc = scale_ranges.get(grade, "")

            item_grade = QTableWidgetItem(grade)
            item_grade.setTextAlignment(Qt.AlignCenter)
            item_range = QTableWidgetItem(range_desc)
            item_range.setTextAlignment(Qt.AlignCenter)
            item_count = QTableWidgetItem(str(count))
            item_count.setTextAlignment(Qt.AlignCenter)

            self._dash_dist_table.setItem(row, 0, item_grade)
            self._dash_dist_table.setItem(row, 1, item_range)
            self._dash_dist_table.setItem(row, 2, item_count)

    # -------------------------------------------------------------------------
    # TAB 2: Students Management
    # -------------------------------------------------------------------------

    def _setup_students_tab(self):
        layout = QVBoxLayout(self._students_tab)

        # Search row
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Student:"))
        self._student_search_input = QLineEdit()
        self._student_search_input.setPlaceholderText("Enter student ID or name...")
        self._student_search_input.returnPressed.connect(self._on_search_students)
        search_layout.addWidget(self._student_search_input)

        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self._on_search_students)
        search_layout.addWidget(search_btn)

        clear_search_btn = QPushButton("Show All")
        clear_search_btn.clicked.connect(self._on_clear_search)
        search_layout.addWidget(clear_search_btn)
        layout.addLayout(search_layout)

        # Student table
        self._student_table = QTableWidget(0, 4)
        self._student_table.setHorizontalHeaderLabels(["Student ID", "Name", "Class / Section", "Status"])
        self._student_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._student_table.setSelectionBehavior(QTableWidget.SelectRows)
        self._student_table.setSelectionMode(QTableWidget.SingleSelection)
        self._student_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._student_table.itemSelectionChanged.connect(self._on_student_table_selection)
        layout.addWidget(self._student_table)

        # Forms area: Add & Edit side by side
        forms_layout = QHBoxLayout()

        # Add Box
        add_box = QGroupBox("Add New Student")
        add_form = QFormLayout(add_box)
        self._add_id_input = QLineEdit()
        self._add_name_input = QLineEdit()
        self._add_class_input = QLineEdit()
        add_form.addRow("Student ID*:", self._add_id_input)
        add_form.addRow("Name*:", self._add_name_input)
        add_form.addRow("Class/Section*:", self._add_class_input)
        add_btn = QPushButton("Add Student")
        add_btn.clicked.connect(self._on_add_student)
        add_form.addRow(add_btn)
        forms_layout.addWidget(add_box)

        # Edit Box
        edit_box = QGroupBox("Update Student Details")
        edit_form = QFormLayout(edit_box)
        self._edit_id_label = QLabel("None selected")
        self._edit_id_label.setStyleSheet("font-weight: bold;")
        self._edit_name_input = QLineEdit()
        self._edit_class_input = QLineEdit()
        edit_form.addRow("Selected ID:", self._edit_id_label)
        edit_form.addRow("New Name:", self._edit_name_input)
        edit_form.addRow("New Class/Section:", self._edit_class_input)

        edit_btns = QHBoxLayout()
        update_btn = QPushButton("Update")
        update_btn.clicked.connect(self._on_update_student)
        delete_btn = QPushButton("Delete Student")
        delete_btn.setStyleSheet("color: #b71c1c;")
        delete_btn.clicked.connect(self._on_delete_student)
        edit_btns.addWidget(update_btn)
        edit_btns.addWidget(delete_btn)
        edit_form.addRow(edit_btns)
        forms_layout.addWidget(edit_box)

        layout.addLayout(forms_layout)

    def refresh_students_table(self, keyword=None):
        results = grade_service.search_students(keyword)
        self._student_table.setRowCount(len(results))
        for row, res in enumerate(results):
            rec = len(config.SUBJECTS) - len(res["missing_subjects"])
            status_text = "Complete" if res["complete"] else f"Incomplete ({rec}/{len(config.SUBJECTS)})"

            item_id = QTableWidgetItem(res["student_id"])
            item_name = QTableWidgetItem(res["name"])
            item_class = QTableWidgetItem(res["class_section"])
            item_status = QTableWidgetItem(status_text)

            self._student_table.setItem(row, 0, item_id)
            self._student_table.setItem(row, 1, item_name)
            self._student_table.setItem(row, 2, item_class)
            self._student_table.setItem(row, 3, item_status)

    def _on_search_students(self):
        kw = self._student_search_input.text().strip()
        self.refresh_students_table(kw)

    def _on_clear_search(self):
        self._student_search_input.clear()
        self.refresh_students_table()

    def _on_student_table_selection(self):
        selected = self._student_table.selectedItems()
        if not selected:
            self._edit_id_label.setText("None selected")
            self._edit_name_input.clear()
            self._edit_class_input.clear()
            return
        row = selected[0].row()
        sid = self._student_table.item(row, 0).text()
        name = self._student_table.item(row, 1).text()
        cls = self._student_table.item(row, 2).text()
        self._edit_id_label.setText(sid)
        self._edit_name_input.setText(name)
        self._edit_class_input.setText(cls)

    def _on_add_student(self):
        sid = self._add_id_input.text()
        name = self._add_name_input.text()
        cls = self._add_class_input.text()
        try:
            student = grade_service.register_student(sid, name, cls)
            self.show_info("Success", f"Student '{student['name']}' ({student['student_id']}) added successfully.")
            self._add_id_input.clear()
            self._add_name_input.clear()
            self._add_class_input.clear()
            self.refresh_all()
        except (ValidationError, grade_service.GradebookError) as err:
            self.show_error(err)

    def _on_update_student(self):
        sid = self._edit_id_label.text()
        if sid == "None selected" or not sid:
            self.show_error("Please select a student from the table first.")
            return
        name = self._edit_name_input.text()
        cls = self._edit_class_input.text()
        try:
            student = grade_service.update_student(sid, name or None, cls or None)
            self.show_info("Success", f"Student '{student['student_id']}' updated successfully.")
            self.refresh_all()
        except (ValidationError, grade_service.GradebookError) as err:
            self.show_error(err)

    def _on_delete_student(self):
        sid = self._edit_id_label.text()
        if sid == "None selected" or not sid:
            self.show_error("Please select a student from the table first.")
            return

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete student '{sid}' and all associated marks?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            grade_service.remove_student(sid)
            self.show_info("Success", f"Student '{sid}' deleted.")
            self._edit_id_label.setText("None selected")
            self._edit_name_input.clear()
            self._edit_class_input.clear()
            self.refresh_all()
        except (ValidationError, grade_service.GradebookError) as err:
            self.show_error(err)

    # -------------------------------------------------------------------------
    # TAB 3: Marks Management
    # -------------------------------------------------------------------------

    def _setup_marks_tab(self):
        layout = QVBoxLayout(self._marks_tab)

        # Student selection row
        sel_box = QGroupBox("Select Student")
        sel_layout = QHBoxLayout(sel_box)
        sel_layout.addWidget(QLabel("Student:"))
        self._marks_student_combo = QComboBox()
        self._marks_student_combo.currentIndexChanged.connect(self._on_marks_student_changed)
        sel_layout.addWidget(self._marks_student_combo, stretch=1)
        layout.addWidget(sel_box)

        # Marks entry form
        self._marks_form_group = QGroupBox("Enter Subject Marks (0 - 100)")
        form_layout = QFormLayout(self._marks_form_group)

        self._mark_inputs = {}
        for subject in config.SUBJECTS:
            inp = QLineEdit()
            inp.setPlaceholderText("Enter mark (0-100) or leave blank")
            form_layout.addRow(f"{subject}:", inp)
            self._mark_inputs[subject] = inp

        btn_layout = QHBoxLayout()
        save_marks_btn = QPushButton("Save Marks")
        save_marks_btn.clicked.connect(self._on_save_marks)
        clear_marks_btn = QPushButton("Clear Fields")
        clear_marks_btn.clicked.connect(self._on_clear_mark_inputs)
        btn_layout.addWidget(save_marks_btn)
        btn_layout.addWidget(clear_marks_btn)
        form_layout.addRow(btn_layout)

        layout.addWidget(self._marks_form_group)
        layout.addStretch()

    def _refresh_marks_combos(self):
        current_id = self._marks_student_combo.currentData()
        self._marks_student_combo.blockSignals(True)
        self._marks_student_combo.clear()
        self._marks_student_combo.addItem("-- Select a student --", None)

        students = grade_service.list_students()
        target_idx = 0
        for idx, s in enumerate(students, start=1):
            text = f"{s['student_id']} - {s['name']} ({s['class_section']})"
            self._marks_student_combo.addItem(text, s["student_id"])
            if s["student_id"] == current_id:
                target_idx = idx

        self._marks_student_combo.setCurrentIndex(target_idx)
        self._marks_student_combo.blockSignals(False)

        if target_idx > 0:
            self._on_marks_student_changed(target_idx)
        else:
            self._on_clear_mark_inputs()

    def _on_marks_student_changed(self, index):
        sid = self._marks_student_combo.currentData()
        if not sid:
            self._on_clear_mark_inputs()
            return
        try:
            result = grade_service.get_student_result(sid)
            for subject in config.SUBJECTS:
                val = result["marks"].get(subject)
                self._mark_inputs[subject].setText("" if val is None else f"{val:g}")
        except (ValidationError, grade_service.GradebookError) as err:
            self.show_error(err)

    def _on_clear_mark_inputs(self):
        for inp in self._mark_inputs.values():
            inp.clear()

    def _on_save_marks(self):
        sid = self._marks_student_combo.currentData()
        if not sid:
            self.show_error("Please select a student first.")
            return

        marks_to_save = {}
        for subject, inp in self._mark_inputs.items():
            text = inp.text().strip()
            if text:
                marks_to_save[subject] = text

        if not marks_to_save:
            self.show_error("No marks were entered.")
            return

        try:
            updated = grade_service.record_marks(sid, marks_to_save)
            self.show_info(
                "Marks Saved",
                f"Marks saved successfully for {updated['name']} ({sid}).\n"
                f"Status: {'Complete' if updated['complete'] else 'Incomplete'}",
            )
            self.refresh_all()
        except (ValidationError, grade_service.GradebookError) as err:
            self.show_error(err)

    # -------------------------------------------------------------------------
    # TAB 4: Student Result
    # -------------------------------------------------------------------------

    def _setup_results_tab(self):
        layout = QVBoxLayout(self._results_tab)

        sel_box = QGroupBox("Select Student to View Result")
        sel_layout = QHBoxLayout(sel_box)
        sel_layout.addWidget(QLabel("Student:"))
        self._result_student_combo = QComboBox()
        self._result_student_combo.currentIndexChanged.connect(self._on_result_student_changed)
        sel_layout.addWidget(self._result_student_combo, stretch=1)
        layout.addWidget(sel_box)

        # Student info display
        self._res_info_group = QGroupBox("Student Academic Record")
        info_layout = QVBoxLayout(self._res_info_group)

        self._res_student_details_label = QLabel("No student selected.")
        self._res_student_details_label.setStyleSheet("font-size: 13px; font-weight: bold;")
        info_layout.addWidget(self._res_student_details_label)

        # Marks breakdown table
        self._res_marks_table = QTableWidget(len(config.SUBJECTS), 3)
        self._res_marks_table.setHorizontalHeaderLabels(["Subject", "Mark Obtained", "Maximum Mark"])
        self._res_marks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._res_marks_table.setEditTriggers(QTableWidget.NoEditTriggers)
        info_layout.addWidget(self._res_marks_table)

        # Result calculation card
        self._res_summary_frame = QFrame()
        self._res_summary_frame.setStyleSheet(
            "background-color: #f7f9fa; border: 1px solid #d0d7de; border-radius: 6px; padding: 12px;"
        )
        sum_layout = QGridLayout(self._res_summary_frame)

        self._res_total_label = QLabel("-")
        self._res_avg_label = QLabel("-")
        self._res_pct_label = QLabel("-")
        self._res_grade_label = QLabel("-")
        self._res_status_label = QLabel("-")

        for lbl in (self._res_total_label, self._res_avg_label, self._res_pct_label, self._res_grade_label):
            lbl.setStyleSheet("font-weight: bold; font-size: 14px;")

        sum_layout.addWidget(QLabel("Total Marks:"), 0, 0)
        sum_layout.addWidget(self._res_total_label, 0, 1)
        sum_layout.addWidget(QLabel("Average:"), 0, 2)
        sum_layout.addWidget(self._res_avg_label, 0, 3)

        sum_layout.addWidget(QLabel("Percentage:"), 1, 0)
        sum_layout.addWidget(self._res_pct_label, 1, 1)
        sum_layout.addWidget(QLabel("Grade:"), 1, 2)
        sum_layout.addWidget(self._res_grade_label, 1, 3)

        sum_layout.addWidget(QLabel("Status:"), 2, 0)
        sum_layout.addWidget(self._res_status_label, 2, 1, 1, 3)

        info_layout.addWidget(self._res_summary_frame)
        layout.addWidget(self._res_info_group)

    def _refresh_results_combo(self):
        current_id = self._result_student_combo.currentData()
        self._result_student_combo.blockSignals(True)
        self._result_student_combo.clear()
        self._result_student_combo.addItem("-- Select a student --", None)

        students = grade_service.list_students()
        target_idx = 0
        for idx, s in enumerate(students, start=1):
            text = f"{s['student_id']} - {s['name']} ({s['class_section']})"
            self._result_student_combo.addItem(text, s["student_id"])
            if s["student_id"] == current_id:
                target_idx = idx

        self._result_student_combo.setCurrentIndex(target_idx)
        self._result_student_combo.blockSignals(False)

        if target_idx > 0:
            self._on_result_student_changed(target_idx)
        else:
            self._clear_result_view()

    def _clear_result_view(self):
        self._res_student_details_label.setText("No student selected.")
        for row in range(len(config.SUBJECTS)):
            self._res_marks_table.setItem(row, 0, QTableWidgetItem(""))
            self._res_marks_table.setItem(row, 1, QTableWidgetItem(""))
            self._res_marks_table.setItem(row, 2, QTableWidgetItem(""))
        self._res_total_label.setText("-")
        self._res_avg_label.setText("-")
        self._res_pct_label.setText("-")
        self._res_grade_label.setText("-")
        self._res_status_label.setText("-")

    def _on_result_student_changed(self, index):
        sid = self._result_student_combo.currentData()
        if not sid:
            self._clear_result_view()
            return

        try:
            res = grade_service.get_student_result(sid)
            self._res_student_details_label.setText(
                f"Student: {res['name']}  |  ID: {res['student_id']}  |  Class/Section: {res['class_section']}"
            )

            for row, subject in enumerate(config.SUBJECTS):
                mark = res["marks"].get(subject)
                mark_text = "-" if mark is None else f"{mark:g}"

                it_sub = QTableWidgetItem(subject)
                it_mark = QTableWidgetItem(mark_text)
                it_max = QTableWidgetItem(f"{config.MAX_MARK_PER_SUBJECT:g}")

                it_mark.setTextAlignment(Qt.AlignCenter)
                it_max.setTextAlignment(Qt.AlignCenter)

                self._res_marks_table.setItem(row, 0, it_sub)
                self._res_marks_table.setItem(row, 1, it_mark)
                self._res_marks_table.setItem(row, 2, it_max)

            if res["complete"]:
                self._res_total_label.setText(f"{res['total']:g} / {config.MAX_TOTAL_MARKS:g}")
                self._res_avg_label.setText(f"{res['average']:.2f}")
                self._res_pct_label.setText(f"{res['percentage']:.2f}%")
                self._res_grade_label.setText(f"{res['grade']}")
                self._res_status_label.setText("COMPLETE")
                self._res_status_label.setStyleSheet("color: #1b5e20; font-weight: bold;")
            else:
                self._res_total_label.setText("N/A")
                self._res_avg_label.setText("N/A")
                self._res_pct_label.setText("N/A")
                self._res_grade_label.setText("N/A")
                missing_str = ", ".join(res["missing_subjects"])
                self._res_status_label.setText(
                    f"INCOMPLETE — Missing subjects: {missing_str} (missing marks are not treated as zero)"
                )
                self._res_status_label.setStyleSheet("color: #b71c1c; font-weight: bold;")
        except (ValidationError, grade_service.GradebookError) as err:
            self.show_error(err)

    # -------------------------------------------------------------------------
    # TAB 5: Class Performance Summary
    # -------------------------------------------------------------------------

    def _setup_summary_tab(self):
        layout = QVBoxLayout(self._summary_tab)

        title = QLabel("<h2>Class Performance Summary</h2>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self._sum_stats_label = QLabel("Class Stats: Loading...")
        self._sum_stats_label.setStyleSheet("font-size: 13px; padding: 6px;")
        layout.addWidget(self._sum_stats_label)

        # Table of all students and their performance
        table_group = QGroupBox("Student Performance Table")
        table_layout = QVBoxLayout(table_group)
        self._sum_table = QTableWidget(0, 7)
        self._sum_table.setHorizontalHeaderLabels([
            "Student ID", "Name", "Class", "Total Marks", "Average", "Percentage", "Grade"
        ])
        self._sum_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._sum_table.setEditTriggers(QTableWidget.NoEditTriggers)
        table_layout.addWidget(self._sum_table)
        layout.addWidget(table_group)

        refresh_btn = QPushButton("Refresh Summary")
        refresh_btn.clicked.connect(self.refresh_summary)
        layout.addWidget(refresh_btn, alignment=Qt.AlignRight)

    def refresh_summary(self):
        summary = grade_service.get_performance_summary()
        avg_text = f"{summary['class_average']:.2f}%" if summary["class_average"] is not None else "N/A"
        self._sum_stats_label.setText(
            f"<b>Total Students:</b> {summary['student_count']}  |  "
            f"<b>Complete:</b> {summary['graded_count']}  |  "
            f"<b>Incomplete:</b> {summary['incomplete_count']}  |  "
            f"<b>Class Average:</b> {avg_text}"
        )

        all_results = grade_service.get_all_student_results()
        self._sum_table.setRowCount(len(all_results))
        for row, res in enumerate(all_results):
            tot = f"{res['total']:g}" if res["total"] is not None else "Incomplete"
            avg = f"{res['average']:.2f}" if res["average"] is not None else "-"
            pct = f"{res['percentage']:.2f}%" if res["percentage"] is not None else "-"
            grd = res["grade"] if res["grade"] is not None else "-"

            self._sum_table.setItem(row, 0, QTableWidgetItem(res["student_id"]))
            self._sum_table.setItem(row, 1, QTableWidgetItem(res["name"]))
            self._sum_table.setItem(row, 2, QTableWidgetItem(res["class_section"]))

            it_tot = QTableWidgetItem(tot)
            it_avg = QTableWidgetItem(avg)
            it_pct = QTableWidgetItem(pct)
            it_grd = QTableWidgetItem(grd)

            for it in (it_tot, it_avg, it_pct, it_grd):
                it.setTextAlignment(Qt.AlignCenter)

            self._sum_table.setItem(row, 3, it_tot)
            self._sum_table.setItem(row, 4, it_avg)
            self._sum_table.setItem(row, 5, it_pct)
            self._sum_table.setItem(row, 6, it_grd)

    # -------------------------------------------------------------------------
    # Global Refresh & Tab Switch
    # -------------------------------------------------------------------------

    def _on_tab_changed(self, index):
        """Update active tab views when user clicks a tab."""
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.refresh_students_table(self._student_search_input.text().strip())
        elif index == 2:
            self._refresh_marks_combos()
        elif index == 3:
            self._refresh_results_combo()
        elif index == 4:
            self.refresh_summary()

    def refresh_all(self):
        """Refresh all screens and selections."""
        self.refresh_dashboard()
        self.refresh_students_table(self._student_search_input.text().strip())
        self._refresh_marks_combos()
        self._refresh_results_combo()
        self.refresh_summary()
