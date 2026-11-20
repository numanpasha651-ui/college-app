from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    send_file,
    send_from_directory
)

import os
import uuid
import tempfile

from datetime import datetime, timedelta

from dotenv import load_dotenv

import psycopg
from psycopg.rows import dict_row


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# FLASK APP
# =========================================================

app = Flask(__name__)

app.secret_key = os.getenv(
    "SECRET_KEY",
    "temporary-development-secret"
)

app.permanent_session_lifetime = timedelta(days=7)


# =========================================================
# DATABASE
# =========================================================

DATABASE_URL = os.getenv("DATABASE_URL")


# =========================================================
# LOGIN SETTINGS
# =========================================================

STUDENT_LOGIN_ID = os.getenv(
    "STUDENT_LOGIN_ID",
    "Student"
)

STUDENT_PASSWORD = os.getenv(
    "STUDENT_PASSWORD",
    ""
)

TEACHER_LOGIN_ID = os.getenv(
    "TEACHER_LOGIN_ID",
    ""
)

TEACHER_PASSWORD = os.getenv(
    "TEACHER_PASSWORD",
    ""
)

ADMIN_LOGIN_ID = os.getenv(
    "ADMIN_LOGIN_ID",
    "admin"
)

ADMIN_PASSWORD = os.getenv(
    "ADMIN_PASSWORD",
    ""
)


# =========================================================
# COLLEGE SETTINGS
# =========================================================

SECTIONS = [
    "BCA1B1",
    "BCA1B2",
    "BCA1B3",
    "BCA1B4",
    "BCA1B5"
]


SUBJECTS = [
    "C-Programming",
    "PPL",
    "COLD",
    "English",
    "Hindi",
    "Kannada",
    "CV",
    "C-Programming Lab",
    "PPL Lab",
    "COLD Lab"
]


DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday"
]


NOTIFICATION_TYPES = [
    "Teacher Absent",
    "Class Cancelled",
    "Class Changed",
    "Room Changed",
    "Time Changed",
    "Substitute Teacher",
    "Important Notice",
    "Timetable Added",
    "Timetable Changed",
    "Timetable Removed",
    "Other"
]


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    if not DATABASE_URL:

        raise RuntimeError(
            "DATABASE_URL is missing. "
            "Add DATABASE_URL in Render Environment Variables."
        )

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


# =========================================================
# CREATE DATABASE TABLES
# =========================================================

def init_database():

    connection = get_db()

    try:

        cursor = connection.cursor()

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            class_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            subject TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable (
            id SERIAL PRIMARY KEY,
            class_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            teacher TEXT NOT NULL,
            day TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            room TEXT
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id SERIAL PRIMARY KEY,
            class_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            teacher TEXT NOT NULL,
            status TEXT NOT NULL,
            message TEXT NOT NULL,
            change_date TEXT,
            notification_date TEXT
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        student_deleted_notifications (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            notification_id INTEGER NOT NULL,
            UNIQUE(student_id, notification_id)
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        student_notification_status (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            notification_id INTEGER NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            UNIQUE(student_id, notification_id)
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        teacher_deleted_notifications (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL,
            notification_id INTEGER NOT NULL,
            UNIQUE(teacher_id, notification_id)
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        teacher_notification_status (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL,
            notification_id INTEGER NOT NULL,
            is_read INTEGER NOT NULL DEFAULT 0,
            UNIQUE(teacher_id, notification_id)
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS timetable_requests (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL,
            teacher_name TEXT NOT NULL,
            class_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            timetable_id INTEGER,
            requested_day TEXT NOT NULL,
            requested_start_time TEXT NOT NULL,
            requested_end_time TEXT NOT NULL,
            requested_room TEXT,
            reason TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            request_date TEXT NOT NULL,
            admin_message TEXT
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teacher_announcements (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            announcement_date TEXT NOT NULL
        )
        """)


        cursor.execute("""
        CREATE TABLE IF NOT EXISTS
        teacher_deleted_announcements (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL,
            announcement_id INTEGER NOT NULL,
            UNIQUE(teacher_id, announcement_id)
        )
        """)

        connection.commit()

    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# CREATE TABLES WHEN RENDER STARTS
# =========================================================

init_database()


# =========================================================
# HELPERS
# =========================================================

def normalize_section(section):

    if not section:
        return None

    section = section.strip().upper()

    if section in SECTIONS:
        return section

    return None


def normalize_subject(subject):

    if not subject:
        return None

    entered = subject.strip().lower()

    for item in SUBJECTS:

        if item.lower() == entered:
            return item

    return None


def make_email(name, role):

    clean_name = (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace(".", "")
    )

    unique = uuid.uuid4().hex[:8]

    return (
        clean_name
        + "_"
        + unique
        + "@"
        + role
        + ".local"
    )


def add_notification(
    connection,
    class_name,
    subject,
    teacher,
    status,
    message
):

    current_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M"
    )

    connection.execute(
        """
        INSERT INTO notifications
        (
            class_name,
            subject,
            teacher,
            status,
            message,
            change_date,
            notification_date
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            class_name,
            subject,
            teacher,
            status,
            message,
            current_time,
            current_time
        )
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        if "admin_id" in session:
            return redirect("/admin")

        if "teacher_id" in session:
            return redirect("/teacher")

        if "student_id" in session:
            return redirect("/student")


    if request.method == "POST":

        role = request.form.get(
            "role",
            ""
        ).strip().lower()

        login_id = request.form.get(
            "login_id",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        name = request.form.get(
            "name",
            ""
        ).strip()


        # =================================================
        # STUDENT
        # =================================================

        if role == "student":

            if (
                login_id.lower()
                != STUDENT_LOGIN_ID.lower()
                or password != STUDENT_PASSWORD
            ):

                return render_template(
                    "login.html",
                    error="Wrong Student ID or Password."
                )


            section = normalize_section(
                request.form.get(
                    "section",
                    ""
                )
            )


            if not name:

                return render_template(
                    "login.html",
                    error="Please enter your name."
                )


            if not section:

                return render_template(
                    "login.html",
                    error="Please select a valid section."
                )


            connection = get_db()

            try:

                student = connection.execute(
                    """
                    SELECT *
                    FROM students
                    WHERE LOWER(name) = LOWER(%s)
                    AND UPPER(class_name) = %s
                    LIMIT 1
                    """,
                    (
                        name,
                        section
                    )
                ).fetchone()


                if student is None:

                    connection.execute(
                        """
                        INSERT INTO students
                        (
                            name,
                            email,
                            password,
                            class_name,
                            status
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            name,
                            make_email(
                                name,
                                "student"
                            ),
                            STUDENT_PASSWORD,
                            section,
                            "pending"
                        )
                    )

                    connection.commit()


                    student = connection.execute(
                        """
                        SELECT *
                        FROM students
                        WHERE LOWER(name) = LOWER(%s)
                        AND UPPER(class_name) = %s
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (
                            name,
                            section
                        )
                    ).fetchone()


            except Exception:

                connection.rollback()
                raise

            finally:

                connection.close()


            if student is None:

                return render_template(
                    "login.html",
                    error="Student account could not be created."
                )


            if student["status"] != "approved":

                session.clear()

                session.permanent = True

                session["waiting_name"] = student["name"]

                session["waiting_type"] = "Student"

                return redirect("/waiting")


            session.clear()

            session.permanent = True

            session["student_id"] = student["id"]

            return redirect("/student")


        # =================================================
        # TEACHER
        # =================================================

        elif role == "teacher":

            if (
                login_id != TEACHER_LOGIN_ID
                or password != TEACHER_PASSWORD
            ):

                return render_template(
                    "login.html",
                    error="Wrong Teacher ID or Password."
                )


            subject = normalize_subject(
                request.form.get(
                    "subject",
                    ""
                )
            )


            if not name:

                return render_template(
                    "login.html",
                    error="Please enter teacher name."
                )


            if not subject:

                return render_template(
                    "login.html",
                    error="Please select a valid subject."
                )


            connection = get_db()

            try:

                teacher = connection.execute(
                    """
                    SELECT *
                    FROM teachers
                    WHERE LOWER(name) = LOWER(%s)
                    AND LOWER(subject) = LOWER(%s)
                    LIMIT 1
                    """,
                    (
                        name,
                        subject
                    )
                ).fetchone()


                if teacher is None:

                    connection.execute(
                        """
                        INSERT INTO teachers
                        (
                            name,
                            email,
                            password,
                            subject,
                            status
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            name,
                            make_email(
                                name,
                                "teacher"
                            ),
                            TEACHER_PASSWORD,
                            subject,
                            "pending"
                        )
                    )

                    connection.commit()


                    teacher = connection.execute(
                        """
                        SELECT *
                        FROM teachers
                        WHERE LOWER(name) = LOWER(%s)
                        AND LOWER(subject) = LOWER(%s)
                        ORDER BY id DESC
                        LIMIT 1
                        """,
                        (
                            name,
                            subject
                        )
                    ).fetchone()


            except Exception:

                connection.rollback()
                raise

            finally:

                connection.close()


            if teacher is None:

                return render_template(
                    "login.html",
                    error="Teacher account could not be created."
                )


            if teacher["status"] != "approved":

                session.clear()

                session.permanent = True

                session["waiting_name"] = teacher["name"]

                session["waiting_type"] = "Teacher"

                return redirect("/waiting")


            session.clear()

            session.permanent = True

            session["teacher_id"] = teacher["id"]

            return redirect("/teacher")


        # =================================================
        # ADMIN
        # =================================================

        elif role == "admin":

            if (
                login_id != ADMIN_LOGIN_ID
                or password != ADMIN_PASSWORD
            ):

                return render_template(
                    "login.html",
                    error="Wrong Admin ID or Password."
                )


            session.clear()

            session.permanent = True

            session["admin_id"] = 1

            return redirect("/admin")


        return render_template(
            "login.html",
            error="Please select a valid role."
        )


    return render_template(
        "login.html"
    )


# =========================================================
# WAITING PAGE
# =========================================================

@app.route("/waiting")
def waiting():

    if "waiting_name" not in session:
        return redirect("/")

    return render_template(
        "waiting.html",
        name=session.get(
            "waiting_name",
            ""
        ),
        user_type=session.get(
            "waiting_type",
            ""
        )
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@app.route("/student")
def student_dashboard():

    if "student_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        student = connection.execute(
            """
            SELECT *
            FROM students
            WHERE id = %s
            """,
            (
                session["student_id"],
            )
        ).fetchone()


        if (
            student is None
            or student["status"] != "approved"
        ):

            session.clear()
            return redirect("/")


        timetable = connection.execute(
            """
            SELECT *
            FROM timetable
            WHERE UPPER(class_name) = %s

            ORDER BY
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,
            start_time
            """,
            (
                student["class_name"].upper(),
            )
        ).fetchall()


        notifications = connection.execute(
            """
            SELECT
                n.*,
                COALESCE(s.is_read, 0) AS is_read

            FROM notifications n

            LEFT JOIN student_notification_status s
            ON s.notification_id = n.id
            AND s.student_id = %s

            WHERE UPPER(n.class_name) = %s

            AND n.id NOT IN
            (
                SELECT notification_id
                FROM student_deleted_notifications
                WHERE student_id = %s
            )

            ORDER BY n.id DESC
            """,
            (
                student["id"],
                student["class_name"].upper(),
                student["id"]
            )
        ).fetchall()


        unread_count = sum(
            1
            for item in notifications
            if item["is_read"] == 0
        )


    finally:

        connection.close()


    return render_template(
        "student_dashboard.html",
        student=student,
        timetable=timetable,
        notifications=notifications,
        unread_count=unread_count
    )


# =========================================================
# STUDENT MARK READ
# =========================================================

@app.route(
    "/student/notification-read/<int:notification_id>"
)
def student_notification_read(
    notification_id
):

    if "student_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            INSERT INTO student_notification_status
            (
                student_id,
                notification_id,
                is_read
            )
            VALUES (%s, %s, 1)

            ON CONFLICT
            (
                student_id,
                notification_id
            )
            DO UPDATE
            SET is_read = 1
            """,
            (
                session["student_id"],
                notification_id
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/student")


# =========================================================
# STUDENT MARK UNREAD
# =========================================================

@app.route(
    "/student/notification-unread/<int:notification_id>"
)
def student_notification_unread(
    notification_id
):

    if "student_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            INSERT INTO student_notification_status
            (
                student_id,
                notification_id,
                is_read
            )
            VALUES (%s, %s, 0)

            ON CONFLICT
            (
                student_id,
                notification_id
            )
            DO UPDATE
            SET is_read = 0
            """,
            (
                session["student_id"],
                notification_id
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/student")


# =========================================================
# STUDENT MARK ALL READ
# =========================================================

@app.route("/student/mark-all-read")
def student_mark_all_read():

    if "student_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        student = connection.execute(
            """
            SELECT *
            FROM students
            WHERE id = %s
            """,
            (
                session["student_id"],
            )
        ).fetchone()


        if student is None:
            return redirect("/")


        rows = connection.execute(
            """
            SELECT id
            FROM notifications

            WHERE UPPER(class_name) = %s

            AND id NOT IN
            (
                SELECT notification_id
                FROM student_deleted_notifications
                WHERE student_id = %s
            )
            """,
            (
                student["class_name"].upper(),
                student["id"]
            )
        ).fetchall()


        for item in rows:

            connection.execute(
                """
                INSERT INTO student_notification_status
                (
                    student_id,
                    notification_id,
                    is_read
                )
                VALUES (%s, %s, 1)

                ON CONFLICT
                (
                    student_id,
                    notification_id
                )
                DO UPDATE
                SET is_read = 1
                """,
                (
                    student["id"],
                    item["id"]
                )
            )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/student")


# =========================================================
# STUDENT DELETE NOTIFICATION
# =========================================================

@app.route(
    "/student/delete-notification/<int:notification_id>"
)
def student_delete_notification(
    notification_id
):

    if "student_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM student_notification_status
            WHERE student_id = %s
            AND notification_id = %s
            """,
            (
                session["student_id"],
                notification_id
            )
        )


        connection.execute(
            """
            INSERT INTO student_deleted_notifications
            (
                student_id,
                notification_id
            )
            VALUES (%s, %s)

            ON CONFLICT
            (
                student_id,
                notification_id
            )
            DO NOTHING
            """,
            (
                session["student_id"],
                notification_id
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/student")


# =========================================================
# TEACHER DASHBOARD
# =========================================================

@app.route("/teacher")
def teacher_dashboard():

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        teacher = connection.execute(
            """
            SELECT *
            FROM teachers
            WHERE id = %s
            """,
            (
                session["teacher_id"],
            )
        ).fetchone()


        if (
            teacher is None
            or teacher["status"] != "approved"
        ):

            session.clear()
            return redirect("/")


        timetable = connection.execute(
            """
            SELECT *
            FROM timetable

            WHERE LOWER(teacher) = LOWER(%s)
            OR LOWER(subject) = LOWER(%s)

            ORDER BY
            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,
            start_time
            """,
            (
                teacher["name"],
                teacher["subject"]
            )
        ).fetchall()


        notifications = connection.execute(
            """
            SELECT
                n.*,
                COALESCE(s.is_read, 0) AS is_read

            FROM notifications n

            LEFT JOIN teacher_notification_status s
            ON s.notification_id = n.id
            AND s.teacher_id = %s

            WHERE LOWER(n.teacher) = LOWER(%s)

            AND n.id NOT IN
            (
                SELECT notification_id
                FROM teacher_deleted_notifications
                WHERE teacher_id = %s
            )

            ORDER BY n.id DESC
            """,
            (
                teacher["id"],
                teacher["name"],
                teacher["id"]
            )
        ).fetchall()


        unread_count = sum(
            1
            for item in notifications
            if item["is_read"] == 0
        )


        requests = connection.execute(
            """
            SELECT *
            FROM timetable_requests
            WHERE teacher_id = %s
            ORDER BY id DESC
            """,
            (
                teacher["id"],
            )
        ).fetchall()


        latest_decision = connection.execute(
            """
            SELECT *
            FROM timetable_requests

            WHERE teacher_id = %s

            AND status IN
            (
                'approved',
                'rejected'
            )

            ORDER BY id DESC

            LIMIT 1
            """,
            (
                teacher["id"],
            )
        ).fetchone()


        teacher_announcements = connection.execute(
            """
            SELECT a.*
            FROM teacher_announcements a

            WHERE a.id NOT IN
            (
                SELECT announcement_id
                FROM teacher_deleted_announcements
                WHERE teacher_id = %s
            )

            ORDER BY a.id DESC
            """,
            (
                teacher["id"],
            )
        ).fetchall()


    finally:

        connection.close()


    return render_template(
        "teacher_dashboard.html",
        teacher=teacher,
        timetable=timetable,
        notifications=notifications,
        unread_count=unread_count,
        requests=requests,
        latest_decision=latest_decision,
        teacher_announcements=teacher_announcements
    )


# =========================================================
# TEACHER MARK READ
# =========================================================

@app.route(
    "/teacher/notification-read/<int:notification_id>"
)
def teacher_notification_read(
    notification_id
):

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            INSERT INTO teacher_notification_status
            (
                teacher_id,
                notification_id,
                is_read
            )
            VALUES (%s, %s, 1)

            ON CONFLICT
            (
                teacher_id,
                notification_id
            )
            DO UPDATE
            SET is_read = 1
            """,
            (
                session["teacher_id"],
                notification_id
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# TEACHER MARK UNREAD
# =========================================================

@app.route(
    "/teacher/notification-unread/<int:notification_id>"
)
def teacher_notification_unread(
    notification_id
):

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            INSERT INTO teacher_notification_status
            (
                teacher_id,
                notification_id,
                is_read
            )
            VALUES (%s, %s, 0)

            ON CONFLICT
            (
                teacher_id,
                notification_id
            )
            DO UPDATE
            SET is_read = 0
            """,
            (
                session["teacher_id"],
                notification_id
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# TEACHER MARK ALL READ
# =========================================================

@app.route("/teacher/mark-all-read")
def teacher_mark_all_read():

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        teacher = connection.execute(
            """
            SELECT *
            FROM teachers
            WHERE id = %s
            """,
            (
                session["teacher_id"],
            )
        ).fetchone()


        if teacher is None:
            return redirect("/")


        rows = connection.execute(
            """
            SELECT id
            FROM notifications

            WHERE LOWER(teacher) = LOWER(%s)

            AND id NOT IN
            (
                SELECT notification_id
                FROM teacher_deleted_notifications
                WHERE teacher_id = %s
            )
            """,
            (
                teacher["name"],
                teacher["id"]
            )
        ).fetchall()


        for item in rows:

            connection.execute(
                """
                INSERT INTO teacher_notification_status
                (
                    teacher_id,
                    notification_id,
                    is_read
                )
                VALUES (%s, %s, 1)

                ON CONFLICT
                (
                    teacher_id,
                    notification_id
                )
                DO UPDATE
                SET is_read = 1
                """,
                (
                    teacher["id"],
                    item["id"]
                )
            )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# TEACHER DELETE NOTIFICATION
# =========================================================

@app.route(
    "/teacher/delete-notification/<int:notification_id>"
)
def teacher_delete_notification(
    notification_id
):

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM teacher_notification_status
            WHERE teacher_id = %s
            AND notification_id = %s
            """,
            (
                session["teacher_id"],
                notification_id
            )
        )


        connection.execute(
            """
            INSERT INTO teacher_deleted_notifications
            (
                teacher_id,
                notification_id
            )
            VALUES (%s, %s)

            ON CONFLICT
            (
                teacher_id,
                notification_id
            )
            DO NOTHING
            """,
            (
                session["teacher_id"],
                notification_id
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# TEACHER DELETE ANNOUNCEMENT
# =========================================================

@app.route(
    "/teacher/delete-announcement/<int:announcement_id>"
)
def teacher_delete_announcement(
    announcement_id
):

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            INSERT INTO teacher_deleted_announcements
            (
                teacher_id,
                announcement_id
            )
            VALUES (%s, %s)

            ON CONFLICT
            (
                teacher_id,
                announcement_id
            )
            DO NOTHING
            """,
            (
                session["teacher_id"],
                announcement_id
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# TEACHER SEND NOTIFICATION
# =========================================================

@app.route(
    "/teacher/notification",
    methods=["GET", "POST"]
)
def teacher_notification():

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        teacher = connection.execute(
            """
            SELECT *
            FROM teachers
            WHERE id = %s
            """,
            (
                session["teacher_id"],
            )
        ).fetchone()


        if (
            teacher is None
            or teacher["status"] != "approved"
        ):

            return redirect("/")


        if request.method == "POST":

            section = normalize_section(
                request.form.get(
                    "class_name",
                    ""
                )
            )

            subject = normalize_subject(
                request.form.get(
                    "subject",
                    ""
                )
            )

            status = request.form.get(
                "status",
                ""
            ).strip()

            message = request.form.get(
                "message",
                ""
            ).strip()


            if (
                not section
                or not subject
                or status not in NOTIFICATION_TYPES
                or not message
            ):

                return render_template(
                    "teacher_notification.html",
                    error="Please enter valid information.",
                    sections=SECTIONS,
                    subjects=SUBJECTS,
                    statuses=NOTIFICATION_TYPES
                )


            add_notification(
                connection,
                section,
                subject,
                teacher["name"],
                status,
                message
            )

            connection.commit()

            return redirect("/teacher")


        return render_template(
            "teacher_notification.html",
            sections=SECTIONS,
            subjects=SUBJECTS,
            statuses=NOTIFICATION_TYPES
        )


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# TEACHER TIMETABLE CHANGE REQUEST
# =========================================================

@app.route(
    "/teacher/request-change",
    methods=["GET", "POST"]
)
def request_timetable_change():

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        teacher = connection.execute(
            """
            SELECT *
            FROM teachers
            WHERE id = %s
            """,
            (
                session["teacher_id"],
            )
        ).fetchone()


        if (
            teacher is None
            or teacher["status"] != "approved"
        ):

            return redirect("/")


        teacher_timetable = connection.execute(
            """
            SELECT *
            FROM timetable

            WHERE LOWER(teacher) = LOWER(%s)
            OR LOWER(subject) = LOWER(%s)

            ORDER BY day, start_time
            """,
            (
                teacher["name"],
                teacher["subject"]
            )
        ).fetchall()


        if request.method == "POST":

            timetable_id_text = request.form.get(
                "timetable_id",
                ""
            ).strip()

            requested_day = request.form.get(
                "requested_day",
                ""
            ).strip()

            requested_start_time = request.form.get(
                "requested_start_time",
                ""
            ).strip()

            requested_end_time = request.form.get(
                "requested_end_time",
                ""
            ).strip()

            requested_room = request.form.get(
                "requested_room",
                ""
            ).strip()

            reason = request.form.get(
                "reason",
                ""
            ).strip()


            if not timetable_id_text.isdigit():

                return render_template(
                    "request_timetable_change.html",
                    teacher=teacher,
                    timetable=teacher_timetable,
                    days=DAYS,
                    error="Please select a timetable."
                )


            timetable_id = int(
                timetable_id_text
            )


            selected = connection.execute(
                """
                SELECT *
                FROM timetable

                WHERE id = %s

                AND
                (
                    LOWER(teacher) = LOWER(%s)
                    OR LOWER(subject) = LOWER(%s)
                )

                LIMIT 1
                """,
                (
                    timetable_id,
                    teacher["name"],
                    teacher["subject"]
                )
            ).fetchone()


            if selected is None:

                return render_template(
                    "request_timetable_change.html",
                    teacher=teacher,
                    timetable=teacher_timetable,
                    days=DAYS,
                    error="Invalid timetable."
                )


            if (
                requested_day not in DAYS
                or not requested_start_time
                or not requested_end_time
                or not reason
            ):

                return render_template(
                    "request_timetable_change.html",
                    teacher=teacher,
                    timetable=teacher_timetable,
                    days=DAYS,
                    error="Please fill all required fields."
                )


            connection.execute(
                """
                INSERT INTO timetable_requests
                (
                    teacher_id,
                    teacher_name,
                    class_name,
                    subject,
                    timetable_id,
                    requested_day,
                    requested_start_time,
                    requested_end_time,
                    requested_room,
                    reason,
                    status,
                    request_date,
                    admin_message
                )

                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    teacher["id"],
                    teacher["name"],
                    selected["class_name"],
                    selected["subject"],
                    selected["id"],
                    requested_day,
                    requested_start_time,
                    requested_end_time,
                    requested_room,
                    reason,
                    "pending",
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    ""
                )
            )


            connection.commit()

            return redirect("/teacher")


        return render_template(
            "request_timetable_change.html",
            teacher=teacher,
            timetable=teacher_timetable,
            days=DAYS
        )


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# TEACHER CANCEL REQUEST
# =========================================================

@app.route(
    "/teacher/cancel-request/<int:request_id>"
)
def teacher_cancel_request(
    request_id
):

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM timetable_requests
            WHERE id = %s
            AND teacher_id = %s
            AND status = 'pending'
            """,
            (
                request_id,
                session["teacher_id"]
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# TEACHER DELETE REQUEST HISTORY
# =========================================================

@app.route(
    "/teacher/delete-request/<int:request_id>"
)
def teacher_delete_request(
    request_id
):

    if "teacher_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM timetable_requests

            WHERE id = %s

            AND teacher_id = %s

            AND status != 'pending'
            """,
            (
                request_id,
                session["teacher_id"]
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/teacher")


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route("/admin")
def admin_dashboard():

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        students = connection.execute(
            """
            SELECT *
            FROM students
            ORDER BY class_name, name
            """
        ).fetchall()


        teachers = connection.execute(
            """
            SELECT *
            FROM teachers
            ORDER BY name
            """
        ).fetchall()


        timetable = connection.execute(
            """
            SELECT *
            FROM timetable

            ORDER BY
            class_name,

            CASE day
                WHEN 'Monday' THEN 1
                WHEN 'Tuesday' THEN 2
                WHEN 'Wednesday' THEN 3
                WHEN 'Thursday' THEN 4
                WHEN 'Friday' THEN 5
                WHEN 'Saturday' THEN 6
                ELSE 7
            END,

            start_time
            """
        ).fetchall()


        notifications = connection.execute(
            """
            SELECT *
            FROM notifications
            ORDER BY id DESC
            """
        ).fetchall()


        change_requests = connection.execute(
            """
            SELECT *
            FROM timetable_requests

            WHERE status = 'pending'

            ORDER BY id DESC
            """
        ).fetchall()


        student_announcements = connection.execute(
            """
            SELECT *
            FROM notifications

            WHERE teacher = 'Admin'
            AND status = 'Announcement'

            ORDER BY id DESC
            """
        ).fetchall()


        teacher_announcements = connection.execute(
            """
            SELECT *
            FROM teacher_announcements
            ORDER BY id DESC
            """
        ).fetchall()


    finally:

        connection.close()


    return render_template(
        "admin_dashboard.html",
        students=students,
        teachers=teachers,
        timetable=timetable,
        notifications=notifications,
        change_requests=change_requests,
        student_announcements=student_announcements,
        teacher_announcements=teacher_announcements
    )


# =========================================================
# MANAGE STUDENTS
# =========================================================

@app.route("/admin/students")
def admin_students():

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        students = connection.execute(
            """
            SELECT *
            FROM students

            ORDER BY
            CASE status
                WHEN 'pending' THEN 1
                ELSE 2
            END,
            class_name,
            name
            """
        ).fetchall()

    finally:

        connection.close()


    return render_template(
        "manage_students.html",
        students=students
    )


# =========================================================
# APPROVE STUDENT
# =========================================================

@app.route(
    "/admin/approve-student/<int:student_id>"
)
def approve_student(
    student_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            UPDATE students
            SET status = 'approved'
            WHERE id = %s
            """,
            (
                student_id,
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# DELETE STUDENT
# =========================================================

@app.route(
    "/admin/delete-student/<int:student_id>"
)
def delete_student(
    student_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM student_deleted_notifications
            WHERE student_id = %s
            """,
            (
                student_id,
            )
        )


        connection.execute(
            """
            DELETE FROM student_notification_status
            WHERE student_id = %s
            """,
            (
                student_id,
            )
        )


        connection.execute(
            """
            DELETE FROM students
            WHERE id = %s
            """,
            (
                student_id,
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# MANAGE TEACHERS
# =========================================================

@app.route("/admin/teachers")
def admin_teachers():

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        teachers = connection.execute(
            """
            SELECT *
            FROM teachers

            ORDER BY
            CASE status
                WHEN 'pending' THEN 1
                ELSE 2
            END,
            name
            """
        ).fetchall()

    finally:

        connection.close()


    return render_template(
        "manage_teachers.html",
        teachers=teachers
    )


# =========================================================
# APPROVE TEACHER
# =========================================================

@app.route(
    "/admin/approve-teacher/<int:teacher_id>"
)
def approve_teacher(
    teacher_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            UPDATE teachers
            SET status = 'approved'
            WHERE id = %s
            """,
            (
                teacher_id,
            )
        )

        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# DELETE TEACHER
# =========================================================

@app.route(
    "/admin/delete-teacher/<int:teacher_id>"
)
def delete_teacher(
    teacher_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM timetable_requests
            WHERE teacher_id = %s
            """,
            (
                teacher_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teacher_deleted_announcements
            WHERE teacher_id = %s
            """,
            (
                teacher_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teacher_notification_status
            WHERE teacher_id = %s
            """,
            (
                teacher_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teacher_deleted_notifications
            WHERE teacher_id = %s
            """,
            (
                teacher_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teachers
            WHERE id = %s
            """,
            (
                teacher_id,
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# ADMIN ADD TEACHER
# =========================================================

@app.route(
    "/admin/add-teacher",
    methods=["GET", "POST"]
)
def add_teacher():

    if "admin_id" not in session:
        return redirect("/")


    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        subject = normalize_subject(
            request.form.get(
                "subject",
                ""
            )
        )


        if not name or not subject:

            return render_template(
                "add_teacher.html",
                error="Please enter valid teacher information.",
                subjects=SUBJECTS
            )


        connection = get_db()

        try:

            existing = connection.execute(
                """
                SELECT *
                FROM teachers

                WHERE LOWER(name) = LOWER(%s)
                AND LOWER(subject) = LOWER(%s)

                LIMIT 1
                """,
                (
                    name,
                    subject
                )
            ).fetchone()


            if existing:

                return render_template(
                    "add_teacher.html",
                    error="Teacher already exists.",
                    subjects=SUBJECTS
                )


            connection.execute(
                """
                INSERT INTO teachers
                (
                    name,
                    email,
                    password,
                    subject,
                    status
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    name,
                    make_email(
                        name,
                        "teacher"
                    ),
                    TEACHER_PASSWORD,
                    subject,
                    "approved"
                )
            )


            connection.commit()


        except Exception:

            connection.rollback()
            raise

        finally:

            connection.close()


        return redirect("/admin/teachers")


    return render_template(
        "add_teacher.html",
        subjects=SUBJECTS
    )


# =========================================================
# ADD TIMETABLE
# =========================================================

@app.route(
    "/admin/add-timetable",
    methods=["GET", "POST"]
)
def add_timetable():

    if "admin_id" not in session:
        return redirect("/")


    if request.method == "POST":

        section = normalize_section(
            request.form.get(
                "class_name",
                ""
            )
        )

        subject = normalize_subject(
            request.form.get(
                "subject",
                ""
            )
        )

        teacher = request.form.get(
            "teacher",
            ""
        ).strip()

        day = request.form.get(
            "day",
            ""
        ).strip()

        start_time = request.form.get(
            "start_time",
            ""
        ).strip()

        end_time = request.form.get(
            "end_time",
            ""
        ).strip()

        room = request.form.get(
            "room",
            ""
        ).strip()


        if (
            not section
            or not subject
            or not teacher
            or day not in DAYS
            or not start_time
            or not end_time
        ):

            return render_template(
                "add_timetable.html",
                error="Please enter valid timetable information.",
                sections=SECTIONS,
                subjects=SUBJECTS,
                days=DAYS
            )


        connection = get_db()

        try:

            connection.execute(
                """
                INSERT INTO timetable
                (
                    class_name,
                    subject,
                    teacher,
                    day,
                    start_time,
                    end_time,
                    room
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    section,
                    subject,
                    teacher,
                    day,
                    start_time,
                    end_time,
                    room
                )
            )


            add_notification(
                connection,
                section,
                subject,
                "Admin",
                "Timetable Added",
                (
                    "New timetable added.\n\n"
                    + "Subject: "
                    + subject
                    + "\nTeacher: "
                    + teacher
                    + "\nDay: "
                    + day
                    + "\nTime: "
                    + start_time
                    + " - "
                    + end_time
                    + "\nRoom: "
                    + (
                        room
                        if room
                        else "Not Assigned"
                    )
                )
            )


            connection.commit()


        except Exception:

            connection.rollback()
            raise

        finally:

            connection.close()


        return redirect("/admin")


    return render_template(
        "add_timetable.html",
        sections=SECTIONS,
        subjects=SUBJECTS,
        days=DAYS
    )


# =========================================================
# EDIT TIMETABLE
# =========================================================

@app.route(
    "/admin/edit-timetable/<int:item_id>",
    methods=["GET", "POST"]
)
def edit_timetable(
    item_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        item = connection.execute(
            """
            SELECT *
            FROM timetable
            WHERE id = %s
            """,
            (
                item_id,
            )
        ).fetchone()


        if item is None:
            return "Timetable not found.", 404


        if request.method == "POST":

            section = normalize_section(
                request.form.get(
                    "class_name",
                    ""
                )
            )

            subject = normalize_subject(
                request.form.get(
                    "subject",
                    ""
                )
            )

            teacher = request.form.get(
                "teacher",
                ""
            ).strip()

            day = request.form.get(
                "day",
                ""
            ).strip()

            start_time = request.form.get(
                "start_time",
                ""
            ).strip()

            end_time = request.form.get(
                "end_time",
                ""
            ).strip()

            room = request.form.get(
                "room",
                ""
            ).strip()


            if (
                not section
                or not subject
                or not teacher
                or day not in DAYS
                or not start_time
                or not end_time
            ):

                return render_template(
                    "edit_timetable.html",
                    item=item,
                    error="Invalid timetable information.",
                    sections=SECTIONS,
                    subjects=SUBJECTS,
                    days=DAYS
                )


            old_section = item["class_name"]

            old_subject = item["subject"]

            old_teacher = item["teacher"]

            old_day = item["day"]

            old_start = item["start_time"]

            old_end = item["end_time"]

            old_room = item["room"] or ""


            connection.execute(
                """
                UPDATE timetable

                SET
                    class_name = %s,
                    subject = %s,
                    teacher = %s,
                    day = %s,
                    start_time = %s,
                    end_time = %s,
                    room = %s

                WHERE id = %s
                """,
                (
                    section,
                    subject,
                    teacher,
                    day,
                    start_time,
                    end_time,
                    room,
                    item_id
                )
            )


            message = (
                "Timetable has been updated.\n\n"
                + "Old Section: "
                + old_section
                + "\nNew Section: "
                + section
                + "\nOld Subject: "
                + old_subject
                + "\nNew Subject: "
                + subject
                + "\nOld Teacher: "
                + old_teacher
                + "\nNew Teacher: "
                + teacher
                + "\nOld Day: "
                + old_day
                + "\nNew Day: "
                + day
                + "\nOld Time: "
                + old_start
                + " - "
                + old_end
                + "\nNew Time: "
                + start_time
                + " - "
                + end_time
                + "\nOld Room: "
                + (
                    old_room
                    if old_room
                    else "Not Assigned"
                )
                + "\nNew Room: "
                + (
                    room
                    if room
                    else "Not Assigned"
                )
            )


            add_notification(
                connection,
                section,
                subject,
                "Admin",
                "Timetable Changed",
                message
            )


            connection.commit()

            return redirect("/admin")


        return render_template(
            "edit_timetable.html",
            item=item,
            sections=SECTIONS,
            subjects=SUBJECTS,
            days=DAYS
        )


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# DELETE TIMETABLE
# =========================================================

@app.route(
    "/admin/delete-timetable/<int:item_id>"
)
def delete_timetable(
    item_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        item = connection.execute(
            """
            SELECT *
            FROM timetable
            WHERE id = %s
            """,
            (
                item_id,
            )
        ).fetchone()


        if item:

            connection.execute(
                """
                DELETE FROM timetable
                WHERE id = %s
                """,
                (
                    item_id,
                )
            )


            add_notification(
                connection,
                item["class_name"],
                item["subject"],
                "Admin",
                "Timetable Removed",
                (
                    item["subject"]
                    + " timetable has been removed.\n\n"
                    + "Teacher: "
                    + item["teacher"]
                    + "\nDay: "
                    + item["day"]
                    + "\nTime: "
                    + item["start_time"]
                    + " - "
                    + item["end_time"]
                )
            )


            connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# ADMIN REVIEW TIMETABLE REQUEST
# =========================================================

@app.route(
    "/admin/review-request/<int:request_id>",
    methods=["GET", "POST"]
)
def review_timetable_request(
    request_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        change_request = connection.execute(
            """
            SELECT *
            FROM timetable_requests
            WHERE id = %s
            """,
            (
                request_id,
            )
        ).fetchone()


        if change_request is None:

            return redirect("/admin")


        timetable_item = None


        if change_request["timetable_id"]:

            timetable_item = connection.execute(
                """
                SELECT *
                FROM timetable
                WHERE id = %s
                """,
                (
                    change_request["timetable_id"],
                )
            ).fetchone()


        if request.method == "POST":

            decision = request.form.get(
                "decision",
                ""
            ).strip().lower()

            admin_message = request.form.get(
                "admin_message",
                ""
            ).strip()


            if not admin_message:

                return render_template(
                    "review_timetable_request.html",
                    item=change_request,
                    timetable_item=timetable_item,
                    error="Please enter an Admin message."
                )


            if decision == "approve":

                if timetable_item is None:

                    return render_template(
                        "review_timetable_request.html",
                        item=change_request,
                        timetable_item=timetable_item,
                        error="Original timetable no longer exists."
                    )


                new_room = (
                    change_request["requested_room"]
                    if change_request["requested_room"]
                    else timetable_item["room"]
                )


                connection.execute(
                    """
                    UPDATE timetable

                    SET
                        day = %s,
                        start_time = %s,
                        end_time = %s,
                        room = %s

                    WHERE id = %s
                    """,
                    (
                        change_request["requested_day"],
                        change_request[
                            "requested_start_time"
                        ],
                        change_request[
                            "requested_end_time"
                        ],
                        new_room,
                        timetable_item["id"]
                    )
                )


                connection.execute(
                    """
                    UPDATE timetable_requests

                    SET
                        status = 'approved',
                        admin_message = %s

                    WHERE id = %s
                    """,
                    (
                        admin_message,
                        request_id
                    )
                )


                add_notification(
                    connection,
                    change_request["class_name"],
                    change_request["subject"],
                    "Admin",
                    "Timetable Changed",
                    (
                        "Timetable change request approved.\n\n"
                        + "Teacher: "
                        + change_request["teacher_name"]
                        + "\nSubject: "
                        + change_request["subject"]
                        + "\nNew Day: "
                        + change_request["requested_day"]
                        + "\nNew Time: "
                        + change_request[
                            "requested_start_time"
                        ]
                        + " - "
                        + change_request[
                            "requested_end_time"
                        ]
                        + "\nRoom: "
                        + (
                            new_room
                            if new_room
                            else "Not Assigned"
                        )
                    )
                )


                connection.commit()

                return redirect("/admin")


            elif decision == "reject":

                connection.execute(
                    """
                    UPDATE timetable_requests

                    SET
                        status = 'rejected',
                        admin_message = %s

                    WHERE id = %s
                    """,
                    (
                        admin_message,
                        request_id
                    )
                )


                connection.commit()

                return redirect("/admin")


            return render_template(
                "review_timetable_request.html",
                item=change_request,
                timetable_item=timetable_item,
                error="Please choose Approve or Reject."
            )


        return render_template(
            "review_timetable_request.html",
            item=change_request,
            timetable_item=timetable_item
        )


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


# =========================================================
# ADMIN ANNOUNCEMENT
# =========================================================

@app.route(
    "/admin/announcement",
    methods=["GET", "POST"]
)
def admin_announcement():

    if "admin_id" not in session:
        return redirect("/")


    if request.method == "POST":

        audience = request.form.get(
            "audience",
            ""
        ).strip().lower()

        target = request.form.get(
            "target",
            ""
        ).strip().upper()

        title = request.form.get(
            "title",
            ""
        ).strip()

        message = request.form.get(
            "message",
            ""
        ).strip()


        if audience not in [
            "students",
            "teachers",
            "everyone"
        ]:

            return render_template(
                "admin_announcement.html",
                sections=SECTIONS,
                error="Please select an audience."
            )


        if not title:

            return render_template(
                "admin_announcement.html",
                sections=SECTIONS,
                error="Please enter announcement title."
            )


        if not message:

            return render_template(
                "admin_announcement.html",
                sections=SECTIONS,
                error="Please enter announcement message."
            )


        if audience in [
            "students",
            "everyone"
        ]:

            if (
                target != "ALL"
                and target not in SECTIONS
            ):

                return render_template(
                    "admin_announcement.html",
                    sections=SECTIONS,
                    error=(
                        "Please select a section "
                        "or ALL SECTIONS."
                    )
                )


        connection = get_db()

        try:

            current_time = datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )


            full_message = (
                title
                + "\n\n"
                + message
            )


            if audience in [
                "students",
                "everyone"
            ]:

                if target == "ALL":

                    for section in SECTIONS:

                        add_notification(
                            connection,
                            section,
                            "College Announcement",
                            "Admin",
                            "Announcement",
                            full_message
                        )

                else:

                    add_notification(
                        connection,
                        target,
                        "College Announcement",
                        "Admin",
                        "Announcement",
                        full_message
                    )


            if audience in [
                "teachers",
                "everyone"
            ]:

                connection.execute(
                    """
                    INSERT INTO teacher_announcements
                    (
                        title,
                        message,
                        announcement_date
                    )
                    VALUES (%s, %s, %s)
                    """,
                    (
                        title,
                        message,
                        current_time
                    )
                )


            connection.commit()


        except Exception:

            connection.rollback()
            raise

        finally:

            connection.close()


        return redirect("/admin")


    return render_template(
        "admin_announcement.html",
        sections=SECTIONS
    )


# =========================================================
# DELETE STUDENT ANNOUNCEMENT
# =========================================================

@app.route(
    "/admin/delete-announcement/<int:notification_id>"
)
def delete_announcement(
    notification_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM student_deleted_notifications
            WHERE notification_id = %s
            """,
            (
                notification_id,
            )
        )


        connection.execute(
            """
            DELETE FROM student_notification_status
            WHERE notification_id = %s
            """,
            (
                notification_id,
            )
        )


        connection.execute(
            """
            DELETE FROM notifications

            WHERE id = %s
            AND teacher = 'Admin'
            AND status = 'Announcement'
            """,
            (
                notification_id,
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# DELETE TEACHER ANNOUNCEMENT
# =========================================================

@app.route(
    "/admin/delete-teacher-announcement/<int:announcement_id>"
)
def delete_teacher_announcement(
    announcement_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM teacher_deleted_announcements
            WHERE announcement_id = %s
            """,
            (
                announcement_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teacher_announcements
            WHERE id = %s
            """,
            (
                announcement_id,
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# ADMIN DELETE NOTIFICATION
# =========================================================

@app.route(
    "/admin/delete-notification/<int:notification_id>"
)
def admin_delete_notification(
    notification_id
):

    if "admin_id" not in session:
        return redirect("/")


    connection = get_db()

    try:

        connection.execute(
            """
            DELETE FROM student_deleted_notifications
            WHERE notification_id = %s
            """,
            (
                notification_id,
            )
        )


        connection.execute(
            """
            DELETE FROM student_notification_status
            WHERE notification_id = %s
            """,
            (
                notification_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teacher_notification_status
            WHERE notification_id = %s
            """,
            (
                notification_id,
            )
        )


        connection.execute(
            """
            DELETE FROM teacher_deleted_notifications
            WHERE notification_id = %s
            """,
            (
                notification_id,
            )
        )


        connection.execute(
            """
            DELETE FROM notifications
            WHERE id = %s
            """,
            (
                notification_id,
            )
        )


        connection.commit()


    except Exception:

        connection.rollback()
        raise

    finally:

        connection.close()


    return redirect("/admin")


# =========================================================
# NOTIFICATIONS PAGE
# =========================================================

@app.route("/notifications")
def notifications():

    connection = get_db()

    try:

        # =================================================
        # STUDENT
        # =================================================

        if "student_id" in session:

            student = connection.execute(
                """
                SELECT *
                FROM students
                WHERE id = %s
                """,
                (
                    session["student_id"],
                )
            ).fetchone()


            if student is None:
                return redirect("/")


            items = connection.execute(
                """
                SELECT *
                FROM notifications

                WHERE UPPER(class_name) = %s

                AND id NOT IN
                (
                    SELECT notification_id
                    FROM student_deleted_notifications
                    WHERE student_id = %s
                )

                ORDER BY id DESC
                """,
                (
                    student["class_name"].upper(),
                    student["id"]
                )
            ).fetchall()


            return render_template(
                "notifications.html",
                notifications=items,
                user_type="student"
            )


        # =================================================
        # TEACHER
        # =================================================

        if "teacher_id" in session:

            teacher = connection.execute(
                """
                SELECT *
                FROM teachers
                WHERE id = %s
                """,
                (
                    session["teacher_id"],
                )
            ).fetchone()


            if teacher is None:
                return redirect("/")


            items = connection.execute(
                """
                SELECT *
                FROM notifications

                WHERE LOWER(teacher) = LOWER(%s)

                AND id NOT IN
                (
                    SELECT notification_id
                    FROM teacher_deleted_notifications
                    WHERE teacher_id = %s
                )

                ORDER BY id DESC
                """,
                (
                    teacher["name"],
                    teacher["id"]
                )
            ).fetchall()


            return render_template(
                "notifications.html",
                notifications=items,
                user_type="teacher"
            )


        # =================================================
        # ADMIN
        # =================================================

        if "admin_id" in session:

            items = connection.execute(
                """
                SELECT *
                FROM notifications
                ORDER BY id DESC
                """
            ).fetchall()


            return render_template(
                "notifications.html",
                notifications=items,
                user_type="admin"
            )


        return redirect("/")


    finally:

        connection.close()


# =========================================================
# POSTGRESQL BACKUP INFORMATION
# =========================================================

@app.route("/admin/backup")
def admin_backup():

    if "admin_id" not in session:
        return redirect("/")


    text = (
        "College Timetable App Database Information\n\n"
        "The application is using PostgreSQL.\n"
        "The database is stored online.\n\n"
        "Use the Render PostgreSQL dashboard "
        "for database management and backups."
    )


    temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        delete=False,
        encoding="utf-8"
    )


    temp_file.write(text)

    temp_file.close()


    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name="database_information.txt"
    )


# =========================================================
# PWA SERVICE WORKER
# =========================================================

@app.route("/service-worker.js")
def service_worker():

    response = send_from_directory(
        ".",
        "service-worker.js",
        mimetype="application/javascript"
    )

    response.headers[
        "Service-Worker-Allowed"
    ] = "/"

    response.headers[
        "Cache-Control"
    ] = "no-cache"

    return response


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# =========================================================
# LOCAL START
# =========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True,
        use_reloader=False
    )