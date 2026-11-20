import sqlite3

from werkzeug.security import generate_password_hash


connection = sqlite3.connect("college.db")

cursor = connection.cursor()


# ==========================================
# STUDENT PASSWORD
# ==========================================

student_password = generate_password_hash("1234")

cursor.execute(
    """
    UPDATE students
    SET password = ?
    WHERE email = ?
    """,
    (
        student_password,
        "rahul@gmail.com"
    )
)


# ==========================================
# SAVE
# ==========================================

connection.commit()

connection.close()


print("Student password secured!")

print("You can now login using:")

print("Email: rahul@gmail.com")

print("Password: 1234")