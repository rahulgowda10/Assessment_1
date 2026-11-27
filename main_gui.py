"""PySide6 Graphical User Interface entry point for Student Gradebook."""

import sys
from PySide6.QtWidgets import QApplication

from database import schema
from gui.main_window import MainWindow


def main():
    """Initialise database and start PySide6 event loop."""
    schema.initialize_database()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
