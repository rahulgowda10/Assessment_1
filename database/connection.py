"""SQLite connection management.

A single configured database path is used by default, but callers (and the
test suite) may pass an explicit ``db_path``. Foreign-key enforcement is
enabled on *every* connection because SQLite turns it off by default.
"""

import sqlite3
from contextlib import contextmanager

import config

_db_path = config.DATABASE_PATH


def set_database_path(path):
    """Point the application at a different SQLite file."""
    global _db_path
    _db_path = path


def get_database_path():
    """Return the database file currently in use."""
    return _db_path


def get_connection(db_path=None):
    """Open a connection with row access by column name and FKs enabled."""
    connection = sqlite3.connect(str(db_path or _db_path))
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def connection_scope(db_path=None):
    """Yield a connection inside a transaction and always close it."""
    connection = get_connection(db_path)
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
