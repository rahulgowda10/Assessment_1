# Student Gradebook & Performance Analyzer

A desktop application designed to store student academic records and subject marks, calculate performance metrics, and produce class performance summaries. Built with intermediate Python simplicity, featuring both a menu-driven **Command-Line Interface (CLI)** and a modern **PySide6 Graphical User Interface (GUI)** backed by **SQLite**.

```
                 USER
                  │
          ┌───────┴───────┐
          │               │
       CLI UI         PySide6 GUI
    (main_cli.py)    (main_gui.py)
          │               │
          └───────┬───────┘
                  │
           SERVICE / LOGIC
       (core/grade_service.py)
                  │
             REPOSITORY
   (database/student_repository.py)
                  │
              SQLite DB
            (gradebook.db)
```

1. **User Interface Layer (`main_cli.py`, `main_gui.py`, `gui/main_window.py`)**:
   - Handles user input, presents structured tables and metric cards, and displays validation errors.
   - GUI button callbacks and CLI actions invoke the exact same service functions with zero duplicated business logic.
2. **Service / Business Logic Layer (`core/grade_service.py`, `core/validators.py`)**:
   - Enforces business rules, validates all inputs, and computes totals, averages, percentages, letter grades, and rankings.
   - Raises readable application-level exceptions (`ValidationError`, `GradebookError`).
3. **Database / Repository Layer (`database/connection.py`, `database/schema.py`, `database/student_repository.py`)**:
   - Isolates all SQL statements (`?` parameterised queries).
   - Manages connection lifecycle and transaction scopes.
   - Ensures foreign-key enforcement is active on every connection (`PRAGMA foreign_keys = ON`).

---

## 2. Technology Stack

- **Language:** Python 3.10+ (tested on Python 3.14)
- **GUI Toolkit:** PySide6 (Qt for Python)
- **Database:** SQLite (`sqlite3` standard library)
- **Testing:** `unittest` (standard library)
- **Dependency Management:** `requirements.txt`

---

## 3. Project Structure

```text
rahul/
├── config.py                 # Central configuration: subjects, max marks, grade boundaries, DB path
├── main_cli.py               # Menu-driven Command Line Interface
├── main_gui.py               # PySide6 desktop GUI launcher
├── requirements.txt          # Third-party dependencies (PySide6)
├── README.md                 # Project documentation and user guide
│
├── core/
│   ├── __init__.py
│   ├── grade_service.py      # Business logic, calculations, results, and summaries
│   └── validators.py         # Input validation rules (ID, name, class, marks)
│
├── database/
│   ├── __init__.py
│   ├── connection.py         # SQLite connection manager & transaction scopes
│   ├── schema.py             # DDL definitions and auto-initialisation
│   └── student_repository.py # Parameterised SQL CRUD operations
│
├── gui/
    ├── __init__.py
    └── main_window.py        # PySide6 QMainWindow with 5 functional tabs
```

---

## 4. Database Design & Rules

The SQLite database (`gradebook.db`) is automatically initialized on application launch with two tables:

### `students`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `student_id` | TEXT | PRIMARY KEY | Unique identifier for each student |
| `name` | TEXT | NOT NULL | Full name of the student |
| `class_section`| TEXT | NOT NULL | Class, grade, or section |
| `created_at` | TEXT | NOT NULL DEFAULT CURRENT_TIMESTAMP | Registration timestamp |

### `marks`
| Column | Type | Constraints | Description |
|---|---|---|---|
| `mark_id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Surrogate key |
| `student_id` | TEXT | NOT NULL, FOREIGN KEY REFERENCES `students(student_id)` ON DELETE CASCADE | Associated student |
| `subject` | TEXT | NOT NULL | Subject name |
| `mark` | REAL | NOT NULL CHECK (mark >= 0 AND mark <= 100) | Numeric mark between 0 and 100 |

### Key Constraints:
- **Foreign Key Cascading:** `PRAGMA foreign_keys = ON;` is enforced on every SQLite connection. When a student is deleted, all their associated marks in `marks` are automatically deleted.
- **Unique Student-Subject:** A `UNIQUE (student_id, subject)` constraint prevents duplicate marks for the same student in any subject. Mark updates use SQLite's `UPSERT` (`INSERT ... ON CONFLICT DO UPDATE`).

---

## 5. Business Logic & Calculations

### Configured Subjects
Defined centrally in `config.py`:
- `Python`
- `Database`
- `Computer Networks`
- `Web Technology`

Maximum mark per subject: **100.0** (Maximum possible total: **400.0**).

### Formulas
$$\text{Total} = \sum \text{marks}$$
$$\text{Average} = \frac{\text{Total}}{\text{Number of Subjects}}$$
$$\text{Percentage} = \frac{\text{Total}}{\text{Maximum Possible Total}} \times 100$$

### Grade Boundaries
| Percentage Range | Letter Grade |
|---|---|
| 90.00% – 100.00% | **A+** |
| 80.00% – 89.99% | **A** |
| 70.00% – 79.99% | **B** |
| 60.00% – 69.99% | **C** |
| 50.00% – 59.99% | **D** |
| Below 50.00% | **F** |

### Important Business Rule: Incomplete Marks
- If marks are not recorded for all configured subjects, the result is marked **INCOMPLETE**.
- Total, average, percentage, and grade remain `None` (`N/A`) and are not calculated.
- **Missing marks are never treated as zero.** Incomplete records are excluded from class average and rank calculations to prevent skewed academic statistics.

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10 or higher.
- `pip` package manager.

### 1. Create Virtual Environment
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```
---

## 7. Execution Instructions

### Running the CLI Application
To launch the menu-driven command-line interface:
```bash
python main_cli.py
```

CLI Menu:
```text
========== STUDENT GRADEBOOK ==========
1. Add student
2. Enter / update subject marks
3. View all students
4. Search student
5. View student result
6. View class performance summary
7. Update student details
8. Delete student
9. Exit
Enter choice:
```

### Running the PySide6 GUI Application
To launch the desktop graphical interface:
```bash
python main_gui.py
```

GUI Tabs:
1. **Dashboard:** Displays total students, graded students, incomplete students, class average, class highlights (highest/lowest performer), and the full grade distribution breakdown.
2. **Students:** Search student records, view the student table, register new students, update details (name, class/section), and delete students with confirmation dialogs.
3. **Marks:** Select a student and enter/update marks for all configured subjects with clear numeric validation.
4. **Result:** View complete academic breakdown for any student including individual subject marks, total score, average, percentage, and letter grade.
5. **Class Summary:** Complete table of all students with ranked performance and comprehensive summary statistics.
---

## 9. Simplicity-First Intermediate Coding Standard

This project was built specifically for intermediate Python education:
- **Clean Functions & Dictionaries:** Avoids unnecessary metaclasses, abstract factories, or custom ORMs.
- **Direct SQL:** Clean parameterised SQL queries inside `student_repository.py`.
- **Reusable Service Layer:** CLI and GUI are pure presentation layers interacting with `core/grade_service.py`.
- **Zero Hidden Logic:** Program flow is transparent and accessible for any intermediate student to inspect and extend.

## 10. Version Control and GitHub Workflow

Git and GitHub are used throughout the project to manage the source code, keep track of changes, and make collaboration easier. Git helps maintain different versions of the code, while GitHub provides an online platform to store the project and manage development activities.

### Repository Management

The project uses GitHub to organize and manage its source code. The `main` branch contains the latest stable version of the application, while new features and updates are developed in separate branches. Once a feature is completed, it is submitted through a Pull Request so that the changes can be reviewed before being merged into the main branch.

### Branch Naming Convention

To keep the repository organized and make it easier to identify different types of changes, the following branch naming convention is used:

- `main` – Contains the main and stable version of the application.
- `feature/feature-name` – Used when adding new features or functionality.
- `fix/issue-name` – Used for fixing bugs or resolving existing issues.

### Commit Message Convention

Each commit includes a short and meaningful message explaining what has been changed. This makes it easier to understand the project's development history and identify specific updates when needed.

Some examples of commit messages include:

- `Add student registration functionality`
- `Improve subject mark validation`
- `Add GUI dashboard`
- `Update project documentation`
- `Fix incomplete student result calculation`

### Issues and Task Tracking

GitHub Issues are used to keep track of bugs, development tasks, and possible improvements. This helps organize the work, identify problems that need attention, and monitor the progress of planned updates.

### Version Releases

Git tags and GitHub Releases are used to mark stable versions of the application. This makes it easier to identify important project updates, keep track of different releases, and return to an earlier version if necessary.
