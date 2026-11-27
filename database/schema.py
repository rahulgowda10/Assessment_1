"""Database schema creation.

The schema follows the assessment specification: a ``students`` table and a
``marks`` table with a unique ``(student_id, subject)`` constraint and a
cascading foreign key.
"""

from database.connection import connection_scope

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    class_section TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS marks (
    mark_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    mark REAL NOT NULL CHECK (mark >= 0 AND mark <= 100),
    UNIQUE (student_id, subject),
    FOREIGN KEY (student_id)
        REFERENCES students(student_id)
        ON DELETE CASCADE
);
"""


def initialize_database(db_path=None):
    """Create the tables if they do not already exist."""
    with connection_scope(db_path) as connection:
        connection.executescript(SCHEMA)
