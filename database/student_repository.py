"""SQLite queries for students and marks.

Only this module talks SQL. All queries use ``?`` placeholders so user input
is never pasted into a statement.
"""

from database.connection import connection_scope


def add_student(student_id, name, class_section, db_path=None):
    """Insert a student row. Raises sqlite3.IntegrityError for a duplicate ID."""
    with connection_scope(db_path) as connection:
        connection.execute(
            "INSERT INTO students (student_id, name, class_section) VALUES (?, ?, ?)",
            (student_id, name, class_section),
        )
    return get_student(student_id, db_path)


def get_student(student_id, db_path=None):
    """Return one student as a dict, or None."""
    with connection_scope(db_path) as connection:
        row = connection.execute(
            "SELECT student_id, name, class_section, created_at "
            "FROM students WHERE student_id = ?",
            (student_id,),
        ).fetchone()
    return dict(row) if row else None


def get_all_students(db_path=None):
    """Return every student ordered by ID."""
    with connection_scope(db_path) as connection:
        rows = connection.execute(
            "SELECT student_id, name, class_section, created_at "
            "FROM students ORDER BY student_id"
        ).fetchall()
    return [dict(row) for row in rows]


def search_students(keyword, db_path=None):
    """Return students whose ID or name contains the keyword."""
    pattern = f"%{keyword}%"
    with connection_scope(db_path) as connection:
        rows = connection.execute(
            "SELECT student_id, name, class_section, created_at "
            "FROM students "
            "WHERE student_id LIKE ? OR name LIKE ? "
            "ORDER BY student_id",
            (pattern, pattern),
        ).fetchall()
    return [dict(row) for row in rows]


def update_student(student_id, name, class_section, db_path=None):
    """Update name and class/section. Returns the number of changed rows."""
    with connection_scope(db_path) as connection:
        cursor = connection.execute(
            "UPDATE students SET name = ?, class_section = ? WHERE student_id = ?",
            (name, class_section, student_id),
        )
    return cursor.rowcount


def delete_student(student_id, db_path=None):
    """Delete a student; marks are removed by the foreign-key cascade."""
    with connection_scope(db_path) as connection:
        cursor = connection.execute(
            "DELETE FROM students WHERE student_id = ?", (student_id,)
        )
    return cursor.rowcount


def save_marks(student_id, marks, db_path=None):
    """Insert or update marks for one student in a single transaction."""
    rows = [(student_id, subject, mark) for subject, mark in marks.items()]
    with connection_scope(db_path) as connection:
        connection.executemany(
            "INSERT INTO marks (student_id, subject, mark) VALUES (?, ?, ?) "
            "ON CONFLICT(student_id, subject) DO UPDATE SET mark = excluded.mark",
            rows,
        )


def get_marks(student_id, db_path=None):
    """Return {subject: mark} for one student."""
    with connection_scope(db_path) as connection:
        rows = connection.execute(
            "SELECT subject, mark FROM marks WHERE student_id = ?", (student_id,)
        ).fetchall()
    return {row["subject"]: row["mark"] for row in rows}


def get_student_with_marks(student_id, db_path=None):
    """Return one student dict with a 'marks' dictionary, or None."""
    student = get_student(student_id, db_path)
    if student is None:
        return None
    student["marks"] = get_marks(student_id, db_path)
    return student
