import sys
import config
from core import grade_service
from core.validators import ValidationError
from database import schema

MENU = """
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
"""

ERRORS = (ValidationError, grade_service.GradebookError)


def format_mark(mark):
    """Show a mark without a trailing .0, or a dash when not entered."""
    return "-" if mark is None else f"{mark:g}"


def ask(prompt, input_fn):
    """Read one trimmed line of input."""
    return input_fn(prompt).strip()


def print_menu(print_fn):
    print_fn(MENU)


def print_result(result, print_fn):
    """Print subject marks and the calculated result."""
    print_fn("")
    print_fn(f"Student: {result['name']} ({result['student_id']})")
    print_fn(f"Class/section: {result['class_section']}")
    print_fn("-" * 46)
    for subject in config.SUBJECTS:
        print_fn(f"  {subject:<20} {format_mark(result['marks'][subject]):>6}")
    print_fn("-" * 46)

    if not result["complete"]:
        print_fn("Result: INCOMPLETE - not calculated.")
        print_fn("Missing subjects: " + ", ".join(result["missing_subjects"]))
        print_fn("(Missing marks are not treated as zero.)")
        return

    print_fn(f"  {'Total':<20} {result['total']:>6g} / {config.MAX_TOTAL_MARKS:g}")
    print_fn(f"  {'Average':<20} {result['average']:>6.2f}")
    print_fn(f"  {'Percentage':<20} {result['percentage']:>6.2f}%")
    print_fn(f"  {'Grade':<20} {result['grade']:>6}")


def add_student(input_fn, print_fn):
    """Option 1: register a new student."""
    student_id = ask("Student ID: ", input_fn)
    name = ask("Student name: ", input_fn)
    class_section = ask("Class/section: ", input_fn)
    student = grade_service.register_student(student_id, name, class_section)
    print_fn(f"Student '{student['name']}' ({student['student_id']}) added.")


def enter_marks(input_fn, print_fn):
    """Option 2: enter or update subject marks for a student."""
    student_id = ask("Student ID: ", input_fn)
    result = grade_service.get_student_result(student_id)
    print_fn(f"Entering marks for {result['name']} ({result['student_id']}).")

    marks = {}
    for subject in config.SUBJECTS:
        current = result["marks"][subject]
        hint = (
            f"current {format_mark(current)}"
            if current is not None
            else "not entered"
        )
        text = ask(f"{subject} [{hint}] (blank = keep unchanged): ", input_fn)
        if text:
            marks[subject] = text

    if not marks:
        print_fn("No marks were entered.")
        return

    updated = grade_service.record_marks(student_id, marks)
    print_fn(f"Marks saved for {updated['name']}.")
    print_result(updated, print_fn)


def view_students(input_fn, print_fn):
    """Option 3: list every student."""
    results = grade_service.get_all_student_results()
    if not results:
        print_fn("No students registered yet.")
        return

    print_fn("")
    print_fn(f"{'ID':<12} {'Name':<24} {'Class':<12} {'Marks':<9} Status")
    print_fn("-" * 72)
    for result in results:
        recorded = len(config.SUBJECTS) - len(result["missing_subjects"])
        marks_text = f"{recorded}/{len(config.SUBJECTS)}"
        status = "Complete" if result["complete"] else "Incomplete"
        print_fn(
            f"{result['student_id']:<12} {result['name']:<24} "
            f"{result['class_section']:<12} {marks_text:<9} {status}"
        )
    print_fn(f"\nTotal students: {len(results)}")


def search_student(input_fn, print_fn):
    """Option 4: search students by ID or name."""
    keyword = ask("Search by student ID or name: ", input_fn)
    results = grade_service.search_students(keyword)
    if not results:
        print_fn(f"No students matched '{keyword}'.")
        return

    print_fn("")
    print_fn(f"{'ID':<12} {'Name':<24} {'Class':<12} Status")
    print_fn("-" * 62)
    for result in results:
        status = "Complete" if result["complete"] else "Incomplete"
        print_fn(
            f"{result['student_id']:<12} {result['name']:<24} "
            f"{result['class_section']:<12} {status}"
        )


def view_result(input_fn, print_fn):
    """Option 5: show one student's calculated result."""
    student_id = ask("Student ID: ", input_fn)
    print_result(grade_service.get_student_result(student_id), print_fn)


def view_summary(input_fn, print_fn):
    """Option 6: show class performance statistics."""
    summary = grade_service.get_performance_summary()
    print_fn("")
    print_fn("========== CLASS PERFORMANCE SUMMARY ==========")
    print_fn(f"Students: {summary['student_count']}")
    print_fn(f"Complete results: {summary['graded_count']}")
    print_fn(f"Incomplete results: {summary['incomplete_count']}")

    if summary["class_average"] is None:
        print_fn("Class average: not available (no complete results yet)")
        print_fn("Highest / lowest: not available")
    else:
        print_fn(f"Class average: {summary['class_average']:.2f}%")
        highest = summary["highest"]
        lowest = summary["lowest"]
        print_fn(
            f"Highest: {highest['name']} ({highest['student_id']}) "
            f"- {highest['percentage']:.2f}% [{highest['grade']}]"
        )
        print_fn(
            f"Lowest: {lowest['name']} ({lowest['student_id']}) "
            f"- {lowest['percentage']:.2f}% [{lowest['grade']}]"
        )

    print_fn("Grade distribution:")
    for grade, count in summary["grade_distribution"].items():
        print_fn(f"  {grade:<3} {count}")


def update_student(input_fn, print_fn):
    """Option 7: update a student's name or class/section."""
    student_id = ask("Student ID: ", input_fn)
    name = ask("New name (blank = keep current): ", input_fn)
    class_section = ask("New class/section (blank = keep current): ", input_fn)
    student = grade_service.update_student(
        student_id, name or None, class_section or None
    )
    print_fn(
        f"Updated student {student['student_id']}: "
        f"{student['name']} / {student['class_section']}"
    )


def delete_student(input_fn, print_fn):
    """Option 8: delete a student after confirmation."""
    student_id = ask("Student ID: ", input_fn)
    result = grade_service.get_student_result(student_id)
    answer = ask(
        f"Delete {result['name']} ({result['student_id']}) "
        "and all marks? (y/N): ",
        input_fn,
    )
    if answer.lower() != "y":
        print_fn("Deletion cancelled.")
        return
    grade_service.remove_student(student_id)
    print_fn(f"Student '{student_id}' deleted.")


def run(input_fn=input, print_fn=print):
    """Run the menu loop until the user exits or input closes."""
    schema.initialize_database()
    print_fn("Student Gradebook database ready.")

    while True:
        print_menu(print_fn)
        try:
            choice = ask("Enter choice: ", input_fn)
        except EOFError:
            print_fn("\nInput closed. Goodbye.")
            return 0

        try:
            if choice == "1":
                add_student(input_fn, print_fn)
            elif choice == "2":
                enter_marks(input_fn, print_fn)
            elif choice == "3":
                view_students(input_fn, print_fn)
            elif choice == "4":
                search_student(input_fn, print_fn)
            elif choice == "5":
                view_result(input_fn, print_fn)
            elif choice == "6":
                view_summary(input_fn, print_fn)
            elif choice == "7":
                update_student(input_fn, print_fn)
            elif choice == "8":
                delete_student(input_fn, print_fn)
            elif choice == "9":
                print_fn("Goodbye.")
                return 0
            else:
                print_fn("Invalid choice. Enter a number from 1 to 9.")
        except ERRORS as error:
            print_fn(f"Error: {error}")
        except EOFError:
            print_fn("\nInput closed. Goodbye.")
            return 0


def main():
    """Entry point used by ``python main_cli.py``."""
    return run()


if __name__ == "__main__":
    sys.exit(main())
