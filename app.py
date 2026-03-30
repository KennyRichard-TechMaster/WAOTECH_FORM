from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

# =========================
# DATABASE SETUP (SMART)
# =========================

DATABASE_URL = os.getenv("DATABASE_URL")

# LOCAL (SQLite)
if not DATABASE_URL:
    import sqlite3

    def get_db_connection():
        conn = sqlite3.connect("school.db")
        conn.row_factory = sqlite3.Row
        return conn

    DB_TYPE = "sqlite"

# RENDER (PostgreSQL)
else:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

    def get_db_connection():
        return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

    DB_TYPE = "postgres"


# =========================
# ADMIN USERS
# =========================

ADMIN_USERS = {
    "Kenny": "1234richard",
    "Remilekun": "Cybersecurity4321"
}


# =========================
# INIT DATABASE
# =========================

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # registrations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id SERIAL PRIMARY KEY,
            full_name TEXT,
            email TEXT,
            phone TEXT,
            gender TEXT,
            age INTEGER,
            address TEXT,
            course TEXT,
            price TEXT,
            preferred_time TEXT,
            created_at TEXT
        )
    """)

    # courses table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price TEXT,
            duration TEXT,
            category TEXT
        )
    """)

    # AUTO ADD COURSES IF EMPTY
    cursor.execute("SELECT COUNT(*) FROM courses")

    if DB_TYPE == "postgres":
        count = cursor.fetchone()['count']
    else:
        count = cursor.fetchone()[0]

    if count == 0:
        default_courses = [
            ("Frontend Development", "₦80,000", "3 Months", "Programming"),
            ("Backend Development", "₦95,000", "3 Months", "Programming"),
            ("Full Stack Development", "₦150,000", "6 Months", "Programming"),
            ("UI/UX Design", "₦70,000", "2 Months", "Design"),
            ("Data Analysis", "₦85,000", "3 Months", "Data"),
            ("Cybersecurity", "₦120,000", "4 Months", "Security"),
        ]

        cursor.executemany("""
            INSERT INTO courses (name, price, duration, category)
            VALUES (?, ?, ?, ?)""" if DB_TYPE == "sqlite" else
            "INSERT INTO courses (name, price, duration, category) VALUES (%s,%s,%s,%s)",
            default_courses
        )

    conn.commit()
    cursor.close()
    conn.close()


# =========================
# HOME
# =========================

@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", courses=courses)


# =========================
# REGISTER
# =========================

@app.route("/register", methods=["POST"])
def register():
    data = request.form
    course_data = data.get("course")

    if not course_data:
        return jsonify({"success": False})

    course_name, price = course_data.split("|")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO registrations 
        (full_name,email,phone,gender,age,address,course,price,preferred_time,created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """ if DB_TYPE == "sqlite" else """
        INSERT INTO registrations 
        (full_name,email,phone,gender,age,address,course,price,preferred_time,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """

    cursor.execute(query, (
        data.get("full_name"),
        data.get("email"),
        data.get("phone"),
        data.get("gender"),
        data.get("age"),
        data.get("address"),
        course_name,
        price,
        data.get("preferred_time"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"success": True})


# =========================
# ADMIN LOGIN
# =========================

@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in ADMIN_USERS and ADMIN_USERS[username] == password:
            session["admin"] = username
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", error="Invalid login")

    return render_template("admin_login.html")


# =========================
# DASHBOARD
# =========================

@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM registrations ORDER BY id DESC")
    regs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin.html", registrations=regs, admin_name=session["admin"])


# =========================
# COURSES PAGE
# =========================

@app.route("/admin/courses")
def admin_courses():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("admin_courses.html", courses=courses)


# =========================
# ADD COURSE
# =========================

@app.route("/admin/add-course", methods=["POST"])
def add_course():
    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "INSERT INTO courses (name, price, duration, category) VALUES (?, ?, ?, ?)" if DB_TYPE == "sqlite" \
        else "INSERT INTO courses (name, price, duration, category) VALUES (%s,%s,%s,%s)"

    cursor.execute(query, (
        data.get("name"),
        data.get("price"),
        data.get("duration"),
        data.get("category")
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_courses"))


# =========================
# UPDATE COURSE
# =========================

@app.route("/admin/update-course/<int:id>", methods=["POST"])
def update_course(id):
    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        UPDATE courses 
        SET name=?, price=?, duration=?, category=? 
        WHERE id=?
    """ if DB_TYPE == "sqlite" else """
        UPDATE courses 
        SET name=%s, price=%s, duration=%s, category=%s 
        WHERE id=%s
    """

    cursor.execute(query, (
        data.get("name"),
        data.get("price"),
        data.get("duration"),
        data.get("category"),
        id
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_courses"))


# =========================
# DELETE COURSE
# =========================

@app.route("/admin/delete-course/<int:id>")
def delete_course(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "DELETE FROM courses WHERE id=?" if DB_TYPE == "sqlite" else "DELETE FROM courses WHERE id=%s"

    cursor.execute(query, (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_courses"))


# =========================
# DELETE REGISTRATION
# =========================

@app.route("/admin/delete-registration/<int:id>")
def delete_registration(id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "DELETE FROM registrations WHERE id=?" if DB_TYPE == "sqlite" else "DELETE FROM registrations WHERE id=%s"

    cursor.execute(query, (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# =========================
# LOGOUT
# =========================

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# =========================
# RUN
# =========================

init_db()

if __name__ == "__main__":
    app.run(debug=True)