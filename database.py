import sqlite3


DATABASE = "college.db"


def create_database():

    connection = sqlite3.connect(
        DATABASE,
        timeout=10
    )

    cursor = connection.cursor()

    connection.execute(
        "PRAGMA busy_timeout = 10000"
    )


    # ==========================================
    # STUDENTS
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        class_name TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    )
    """)


    # ==========================================
    # TEACHERS
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        subject TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending'
    )
    """)


    # ==========================================
    # TIMETABLE
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetable (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        teacher TEXT NOT NULL,
        day TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        room TEXT
    )
    """)


    # ==========================================
    # NOTIFICATIONS
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_name TEXT NOT NULL,
        subject TEXT NOT NULL,
        teacher TEXT NOT NULL,
        status TEXT NOT NULL,
        message TEXT NOT NULL,
        notification_date TEXT NOT NULL
    )
    """)


    # ==========================================
    # STUDENT HIDDEN NOTIFICATIONS
    # ==========================================

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS student_deleted_notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        notification_id INTEGER NOT NULL,
        UNIQUE(student_id, notification_id)
    )
    """)


    # ==========================================
    # UPDATE OLD DATABASE
    # ==========================================

    student_columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(students)"
        ).fetchall()
    ]

    if "status" not in student_columns:

        cursor.execute("""
        ALTER TABLE students
        ADD COLUMN status TEXT
        NOT NULL DEFAULT 'pending'
        """)


    teacher_columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(teachers)"
        ).fetchall()
    ]

    if "status" not in teacher_columns:

        cursor.execute("""
        ALTER TABLE teachers
        ADD COLUMN status TEXT
        NOT NULL DEFAULT 'pending'
        """)


    connection.commit()

    connection.close()

    print("Database ready!")


if __name__ == "__main__":

    create_database()