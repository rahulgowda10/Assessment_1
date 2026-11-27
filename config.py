from pathlib import Path

SUBJECTS = ["Python", "Database", "Computer Networks", "Web Technology"]

MAX_MARK_PER_SUBJECT = 100.0
MAX_TOTAL_MARKS = MAX_MARK_PER_SUBJECT * len(SUBJECTS)

PROJECT_ROOT = Path(__file__).resolve().parent
DATABASE_PATH = PROJECT_ROOT / "gradebook.db"

GRADE_SCALE = [
    (90.0, "A+"),
    (80.0, "A"),
    (70.0, "B"),
    (60.0, "C"),
    (50.0, "D"),
    (0.0, "F"),
]
