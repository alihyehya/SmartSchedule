from flask import Flask, render_template, request
from scheduler import get_schedule_for_student
import mysql.connector
import json
import bcrypt

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        database='smartscheduledb',
        user='root',
        password='project@password123'
    )

@app.route('/', methods=['GET', 'POST'])
def index():
    schedule = []
    alternatives = {}
    student_id = None
    course_colors = {}
    completed_courses = []
    sgpa = ""
    total_credits = 0

    if request.method == 'POST':
        student_id = request.form['student_id']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM student_cache WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()

        if student:
            if bcrypt.checkpw(password.encode(), student['password_hash'].encode()):
                completed_courses = json.loads(student['completed_courses'])
                sgpa = student['sgpa']
                total_credits = student['total_credits']
            else:
                error_message = "Incorrect password."
                return render_template("index.html", error_message=error_message)
        else:
            error_message = "Live scraping not available. Please try again later."
            return render_template("index.html", error_message=error_message)

        cursor.close()
        conn.close()
        schedule, raw_alternatives = get_schedule_for_student(student_id, completed_courses, sgpa, total_credits)
        alternatives = {}
        for code, courses in raw_alternatives.items():
            alternatives[code] = []
            for course in courses:
                alternatives[code].append({
                    "crn": course.crn,
                    "course_code": course.course_code,
                    "name": course.name,
                    "credits": course.credits,
                    "sessions": course.sessions
                })
        unique_codes = {c.course_code for c in schedule}
        palette = [
            "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728",
            "#9467bd", "#8c564b", "#e377c2", "#7f7f7f",
            "#bcbd22", "#17becf", "#f06292", "#4db6ac"
        ]
        for i, code in enumerate(sorted(unique_codes)):
            course_colors[code] = palette[i % len(palette)]

    return render_template("index.html", schedule=schedule, student_id=student_id,
                           course_colors=course_colors, completed_courses=completed_courses,
                           sgpa=sgpa, total_credits=total_credits, alternatives=alternatives)

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

