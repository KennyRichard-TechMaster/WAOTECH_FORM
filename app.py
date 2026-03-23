from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "super_secret_key_change_this"

DATABASE = "school.db"

ADMIN_USERS = {
    "Kenny": "1234richard",
    "Remilekun": "Cybersecurity4321"
}


def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # registrations
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # courses
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price TEXT,
            duration TEXT,
            category TEXT
        )
    """)

    # insert default courses
    cursor.execute("SELECT COUNT(*) FROM courses")
    if cursor.fetchone()[0] == 0:
        courses = [
            ("Frontend Development", "₦80,000", "3 Months", "Programming"),
            ("Backend Development", "₦95,000", "3 Months", "Programming"),
            ("Full Stack Development", "₦150,000", "6 Months", "Programming"),
            ("UI/UX Design", "₦70,000", "2 Months", "Design"),
            ("Data Analysis", "₦85,000", "3 Months", "Data"),
            ("Cybersecurity", "₦120,000", "4 Months", "Security"),
        ]
        cursor.executemany(
            "INSERT INTO courses (name, price, duration, category) VALUES (?, ?, ?, ?)",
            courses
        )

    conn.commit()
    conn.close()


@app.route("/")
def index():
    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()
    return render_template("index.html", courses=courses)


@app.route("/register", methods=["POST"])
def register():
    data = request.form
    course_data = data.get("course")

    course_name, price = course_data.split("|")

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO registrations 
        (full_name,email,phone,gender,age,address,course,price,preferred_time,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?)
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
    conn.close()

    return jsonify({"success": True})


# ADMIN LOGIN
@app.route("/admin-login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username in ADMIN_USERS and ADMIN_USERS[username] == password:
            session["admin"] = username   # ✅ THIS STORES NAME
            return redirect(url_for("admin_dashboard"))

        return render_template("admin_login.html", error="Invalid login")

    return render_template("admin_login.html")


@app.route("/admin")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    regs = conn.execute("SELECT * FROM registrations ORDER BY id DESC").fetchall()
    conn.close()

    return render_template(
        "admin.html",
        registrations=regs,
        admin_name=session["admin"]   
    )


# COURSES MANAGEMENT
@app.route("/admin/courses")
def admin_courses():
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    courses = conn.execute("SELECT * FROM courses").fetchall()
    conn.close()

    return render_template("admin_courses.html", courses=courses)


@app.route("/admin/add-course", methods=["POST"])
def add_course():
    data = request.form

    conn = get_db_connection()
    conn.execute("""
        INSERT INTO courses (name, price, duration, category)
        VALUES (?, ?, ?, ?)
    """, (
        data.get("name"),
        data.get("price"),
        data.get("duration"),
        data.get("category")
    ))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_courses"))


@app.route("/admin/update-course/<int:id>", methods=["POST"])
def update_course(id):
    data = request.form

    conn = get_db_connection()
    conn.execute("""
        UPDATE courses 
        SET name=?, price=?, duration=?, category=? 
        WHERE id=?
    """, (
        data.get("name"),
        data.get("price"),
        data.get("duration"),
        data.get("category"),
        id
    ))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_courses"))


@app.route("/admin/delete-course/<int:id>")
def delete_course(id):
    conn = get_db_connection()
    conn.execute("DELETE FROM courses WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_courses"))
@app.route("/admin/delete-registration/<int:id>")
def delete_registration(id):
    if "admin" not in session:
        return redirect(url_for("admin_login"))

    conn = get_db_connection()
    conn.execute("DELETE FROM registrations WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin_login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)