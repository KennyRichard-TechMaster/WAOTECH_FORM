from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os
import psycopg2
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

# DATABASE CONFIG
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn


ADMIN_USERS = {
    "Kenny": "1234richard",
    "Remilekun": "Cybersecurity4321"
}


# INIT DATABASE
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

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

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id SERIAL PRIMARY KEY,
            name TEXT,
            price TEXT,
            duration TEXT,
            category TEXT
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()


# HOME
@app.route("/")
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM courses")
    courses = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("index.html", courses=courses)


# REGISTER
@app.route("/register", methods=["POST"])
def register():
    data = request.form
    course_data = data.get("course")

    course_name, price = course_data.split("|")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO registrations 
        (full_name,email,phone,gender,age,address,course,price,preferred_time,created_at)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
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


# ADMIN LOGIN
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


# DASHBOARD
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

    return render_template(
        "admin.html",
        registrations=regs,
        admin_name=session["admin"]
    )


# COURSES PAGE
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


# ADD COURSE
@app.route("/admin/add-course", methods=["POST"])
def add_course():
    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO courses (name, price, duration, category)
        VALUES (%s, %s, %s, %s)
    """, (
        data.get("name"),
        data.get("price"),
        data.get("duration"),
        data.get("category")
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_courses"))


# UPDATE COURSE
@app.route("/admin/update-course/<int:id>", methods=["POST"])
def update_course(id):
    data = request.form

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE courses 
        SET name=%s, price=%s, duration=%s, category=%s 
        WHERE id=%s
    """, (
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


# DELETE COURSE
@app.route("/admin/delete-course/<int:id>")
def delete_course(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM courses WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_courses"))


# DELETE REGISTRATION
@app.route("/admin/delete-registration/<int:id>")
def delete_registration(id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM registrations WHERE id=%s", (id,))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("admin_dashboard"))


# LOGOUT
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


# RUN DB INIT
init_db()

if __name__ == "__main__":
    app.run(debug=True)