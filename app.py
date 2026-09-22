from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import mysql.connector 
from dotenv import load_dotenv
import os
import re
 
load_dotenv()
 
app = Flask(__name__) 

app.secret_key = "telwani_secret_key"
 
db = mysql.connector.connect( 
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
) 
 
 
@app.route("/") 
def home(): 
    return render_template("index.html") 
 
 
@app.route("/about") 
def about(): 
    return render_template("about.html") 
 
 
@app.route("/courses") 
def courses(): 
    return render_template("courses.html") 
 
 
@app.route("/learn") 
def learn(): 
    return render_template("learn.html") 
 
 
@app.route("/library") 
def library(): 
    return render_template("library.html") 
 
 
@app.route("/academy") 
def academy(): 
    return render_template("academy.html") 
 
 
@app.route("/questions") 
def questions(): 
    return render_template("que.html") 
 
 
@app.route("/admin") 
def admin(): 
    return render_template("admin.html") 
 
 
@app.route("/registrations") 
def registrations(): 
    return render_template("registrations.html") 
 
 
@app.route("/register", methods=["GET", "POST"]) 
def register(): 
 
    if request.method == "POST": 
 
        fullName = request.form.get("name") 
        age = request.form.get("age") 
        gender = request.form.get("gender") 
        phone = request.form.get("phone") 
        parent_phone = request.form.get("parent_phone")
        phone_pattern = r"^01[0-9]{9}$"

        if not re.fullmatch(phone_pattern, phone or ""):
            return "رقم هاتف الطالب غير صحيح"

        if not re.fullmatch(phone_pattern, parent_phone or ""):
            return "رقم هاتف ولي الأمر غير صحيح"
 
        courses = request.form.getlist("course") 
        course_text = ", ".join(courses) 
 
        way = request.form.get("way") 
        halaqa = request.form.get("halaqa") 
        level = request.form.get("level") 
 
        days = request.form.getlist("day") 
        day_text = ", ".join(days) 
 
        notes = request.form.get("notes") 
 
 
        cursor = db.cursor() 
 
 
        sql = """ 
            INSERT INTO registrations 
            ( 
                fullName, 
                age, 
                gender, 
                phone, 
                parent_phone, 
                course, 
                way, 
                halaqa, 
                level, 
                day, 
                notes 
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
                %s 
            ) 
        """ 
 
 
        values = ( 
            fullName, 
            age, 
            gender, 
            phone, 
            parent_phone, 
            course_text, 
            way, 
            halaqa, 
            level, 
            day_text, 
            notes 
        ) 
 
 
        cursor.execute(sql, values) 
 
        db.commit() 
 
        cursor.close() 
 
 
        return "تم إرسال بيانات التسجيل بنجاح ❤️" 
 
 
    return render_template("register.html") 


@app.route("/admin/registrations/approve/<int:registration_id>", methods=["POST"])
def approve_registration(registration_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # جلب طلب التسجيل
    cursor.execute("""
        SELECT *
        FROM registrations
        WHERE id = %s
    """, (registration_id,))

    registration = cursor.fetchone()

    if not registration:
        cursor.close()
        return "طلب التسجيل غير موجود"

    if registration["status"] == "approved":
        cursor.close()
        return "تم اعتماد هذا الطلب من قبل"

    # التأكد أن رقم الطالب غير مستخدم بالفعل
    cursor.execute("""
        SELECT id
        FROM users
        WHERE phone = %s
    """, (registration["phone"],))

    existing_student = cursor.fetchone()

    if existing_student:
        cursor.close()
        return "رقم هاتف الطالب مستخدم بالفعل في حساب آخر"

    # إنشاء كود الطالب
    student_code = "ST" + str(registration["id"]).zfill(4)

    # التأكد أن كود الطالب غير مستخدم
    cursor.execute("""
        SELECT id
        FROM users
        WHERE student_code = %s
    """, (student_code,))

    if cursor.fetchone():
        cursor.close()
        return "كود الطالب مستخدم بالفعل"

    # --------------------------------
    # إنشاء حساب ولي الأمر
    # --------------------------------

    cursor.execute("""
        SELECT id
        FROM users
        WHERE phone = %s
        AND role = 'parent'
    """, (registration["parent_phone"],))

    parent = cursor.fetchone()

    if not parent:

        cursor.execute("""
            INSERT INTO users
            (
                fullName,
                phone,
                password,
                role
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'parent'
            )
        """, (
            "ولي أمر - " + registration["fullName"],
            registration["parent_phone"],
            "123"
        ))

    # --------------------------------
    # إنشاء حساب الطالب
    # --------------------------------

    cursor.execute("""
        INSERT INTO users
        (
            fullName,
            phone,
            password,
            role,
            student_code,
            parent_phone,
            halaqa,
            level,
            memorized,
            remaining,
            age
        )
        VALUES
        (
            %s,
            %s,
            %s,
            'student',
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        registration["fullName"],
        registration["phone"],
        "123",
        student_code,
        registration["parent_phone"],
        registration["halaqa"],
        registration["level"],
        "",
        "",
        registration["age"]
    ))

    # --------------------------------
    # تحديث حالة طلب التسجيل
    # --------------------------------

    cursor.execute("""
        UPDATE registrations
        SET
            status = 'approved',
            student_code = %s
        WHERE id = %s
    """, (
        student_code,
        registration_id
    ))

    db.commit()

    cursor.close()

    return jsonify({
    "message": "تم اعتماد الطالب وإنشاء الحساب بنجاح",
    "student_code": student_code
})


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        phone = request.form.get("phone")
        password = request.form.get("password")
        phone_pattern = r"^01[0-9]{9}$"

        if not re.fullmatch(phone_pattern, phone or ""):
            return "رقم الهاتف غير صحيح"

        cursor = db.cursor(dictionary=True)

        sql = """
    SELECT id, fullName, phone, password, role
    FROM users
    WHERE phone = %s AND password = %s
"""

        cursor.execute(sql, (phone, password))

        user = cursor.fetchone()

        cursor.close()

        if not user:
            return "رقم الهاتف أو كلمة المرور غير صحيحة"

        session["user_id"] = user["id"]
        session["fullName"] = user["fullName"]
        session["role"] = user["role"]

        if user["role"] == "admin":
            return redirect(url_for("admin_dashboard"))

        elif user["role"] == "teacher":
            return redirect(url_for("teacher_dashboard"))

        elif user["role"] == "student":
            return redirect(url_for("student_dashboard"))

        elif user["role"] == "parent":
            return redirect(url_for("parent_dashboard"))

    return render_template("login.html")

@app.route("/admin/dashboard")
def admin_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    return render_template("admin_dashboard.html")


@app.route("/teacher/dashboard")
def teacher_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT
            students.id,
            students.fullName,
            students.phone,
            students.student_code,
            students.parent_phone,
            students.halaqa,
            students.level,
            students.memorized,
            students.remaining,

            attendance.status AS attendance_status

        FROM users AS students

        LEFT JOIN attendance
            ON attendance.student_id = students.id
            AND attendance.attendance_date = CURDATE()

        WHERE students.role = 'student'
        AND students.teacher_id = %s

        ORDER BY students.fullName
    """

    cursor.execute(sql, (session["user_id"],))

    students = cursor.fetchall()

    cursor.close()

    return render_template(
        "teacher_dashboard.html",
        students=students
    )



@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

@app.route("/student/dashboard")
def student_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "student":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # بيانات الطالب
    cursor.execute("""
        SELECT
            students.id,
            students.fullName,
            students.phone,
            students.student_code,
            students.parent_phone,
            students.halaqa,
            students.level,
            students.memorized,
            students.remaining,
            teachers.fullName AS teacher_name
        FROM users AS students

        LEFT JOIN users AS teachers
            ON students.teacher_id = teachers.id
            AND teachers.role = 'teacher'

        WHERE students.id = %s
        AND students.role = 'student'
    """, (session["user_id"],))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        return "بيانات الطالب غير موجودة"

    # سجل الحضور
    cursor.execute("""
        SELECT
            attendance_date,
            status,
            notes
        FROM attendance
        WHERE student_id = %s
        ORDER BY attendance_date DESC
    """, (student["id"],))

    attendance_records = cursor.fetchall()

    # سجل التسميع
    cursor.execute("""
        SELECT
            date,
            surah,
            from_ayah,
            to_ayah,
            type,
            evaluation,
            notes
        FROM tasmee3
        WHERE student_id = %s
        ORDER BY date DESC, id DESC
    """, (student["id"],))

    tasmee3_records = cursor.fetchall()

    cursor.close()

    return render_template(
        "student_dashboard.html",
        student=student,
        attendance_records=attendance_records,
        tasmee3_records=tasmee3_records
    )


@app.route("/parent/dashboard")
def parent_dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "parent":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # بيانات ولي الأمر
    cursor.execute("""
        SELECT
            id,
            fullName,
            phone
        FROM users
        WHERE id = %s
        AND role = 'parent'
    """, (session["user_id"],))

    parent = cursor.fetchone()

    if not parent:
        cursor.close()
        return "بيانات ولي الأمر غير موجودة"

    # الطلاب المرتبطون برقم هاتف ولي الأمر
    cursor.execute("""
        SELECT
            students.id,
            students.fullName,
            students.student_code,
            students.halaqa,
            students.level,
            students.memorized,
            students.remaining,
            teachers.fullName AS teacher_name
        FROM users AS students

        LEFT JOIN users AS teachers
            ON students.teacher_id = teachers.id
            AND teachers.role = 'teacher'

        WHERE students.role = 'student'
        AND students.parent_phone = %s

        ORDER BY students.fullName
    """, (parent["phone"],))

    children = cursor.fetchall()

    # لكل طالب نجيب الحضور والتسميع
    for child in children:

        cursor.execute("""
            SELECT
                attendance_date,
                status,
                notes
            FROM attendance
            WHERE student_id = %s
            ORDER BY attendance_date DESC
        """, (child["id"],))

        child["attendance_records"] = cursor.fetchall()

        cursor.execute("""
            SELECT
                date,
                surah,
                from_ayah,
                to_ayah,
                type,
                evaluation,
                notes
            FROM tasmee3
            WHERE student_id = %s
            ORDER BY date DESC, id DESC
        """, (child["id"],))

        child["tasmee3_records"] = cursor.fetchall()

    cursor.close()

    return render_template(
        "parent_dashboard.html",
        parent=parent,
        children=children
    )
 
 
@app.route("/api/admin/registrations")
def get_registrations():

    if "user_id" not in session:
        return jsonify({"message": "يجب تسجيل الدخول أولاً"}), 401

    if session["role"] != "admin":
        return jsonify({"message": "ليس لديك صلاحية"}), 403

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            student_code,
            fullName,
            age,
            gender,
            phone,
            parent_phone,
            course,
            way,
            halaqa,
            level,
            day,
            notes,
            created_at,
            status
        FROM registrations
        ORDER BY id DESC
    """)

    registrations = cursor.fetchall()

    cursor.close()

    return jsonify(registrations)
 
@app.route("/api/admin/students", methods=["GET"])
def get_students():

    if "user_id" not in session:
        return jsonify({"message": "يجب تسجيل الدخول أولاً"}), 401

    if session["role"] != "admin":
        return jsonify({"message": "ليس لديك صلاحية"}), 403

    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT
            students.id,
            students.fullName,
            students.phone,
            students.student_code,
            students.parent_phone,
            students.halaqa,
            students.level,
            students.memorized,
            students.remaining,
            teachers.fullName AS teacher_name

        FROM users AS students

        LEFT JOIN users AS teachers
            ON students.teacher_id = teachers.id
            AND teachers.role = 'teacher'

        WHERE students.role = 'student'

        ORDER BY students.id DESC
    """

    cursor.execute(sql)

    students = cursor.fetchall()

    cursor.close()

    return jsonify(students)

@app.route("/admin/students")
def admin_students():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    return render_template("admin_students.html")


@app.route("/admin/students/add", methods=["GET", "POST"])
def add_student():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # =========================
    # إضافة طالب
    # =========================

    if request.method == "POST":

        fullName = request.form.get("fullName")
        phone = request.form.get("phone")
        password = request.form.get("password")
        student_code = request.form.get("student_code")
        parent_phone = request.form.get("parent_phone")
        halaqa = request.form.get("halaqa")
        level = request.form.get("level")
        memorized = request.form.get("memorized")
        remaining = request.form.get("remaining")
        phone_pattern = r"^01[0-9]{9}$"

        if not re.fullmatch(phone_pattern, phone or ""):
            return "رقم هاتف الطالب غير صحيح"

        if not re.fullmatch(phone_pattern, parent_phone or ""):
            return "رقم هاتف ولي الأمر غير صحيح"

        teacher_id = request.form.get("teacher_id") or None

        sql = """
            INSERT INTO users
            (
                fullName,
                phone,
                password,
                role,
                student_code,
                parent_phone,
                halaqa,
                level,
                memorized,
                remaining,
                teacher_id
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'student',
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        cursor.execute(sql, (
            fullName,
            phone,
            password,
            student_code,
            parent_phone,
            halaqa,
            level,
            memorized,
            remaining,
            teacher_id
        ))

        db.commit()

        cursor.close()

        return redirect(url_for("admin_students"))

    # =========================
    # جلب المعلمين
    # =========================

    cursor.execute("""
        SELECT id, fullName
        FROM users
        WHERE role = 'teacher'
        ORDER BY fullName
    """)

    teachers = cursor.fetchall()

    cursor.close()

    return render_template(
        "add_student.html",
        teachers=teachers
    )


@app.route("/admin/students/edit/<int:student_id>", methods=["GET", "POST"])
def edit_student(student_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # =========================
    # تعديل بيانات الطالب
    # =========================

    if request.method == "POST":

        fullName = request.form.get("fullName")
        phone = request.form.get("phone")
        password = request.form.get("password")
        student_code = request.form.get("student_code")
        parent_phone = request.form.get("parent_phone")
        halaqa = request.form.get("halaqa")
        level = request.form.get("level")
        memorized = request.form.get("memorized")
        remaining = request.form.get("remaining")
        phone_pattern = r"^01[0-9]{9}$"

        if not re.fullmatch(phone_pattern, phone or ""):
            return "رقم هاتف الطالب غير صحيح"

        if not re.fullmatch(phone_pattern, parent_phone or ""):
            return "رقم هاتف ولي الأمر غير صحيح"

        teacher_id = request.form.get("teacher_id") or None

        sql = """
            UPDATE users
            SET
                fullName = %s,
                phone = %s,
                password = %s,
                student_code = %s,
                parent_phone = %s,
                halaqa = %s,
                level = %s,
                memorized = %s,
                remaining = %s,
                teacher_id = %s
            WHERE id = %s
            AND role = 'student'
        """

        cursor.execute(sql, (
            fullName,
            phone,
            password,
            student_code,
            parent_phone,
            halaqa,
            level,
            memorized,
            remaining,
            teacher_id,
            student_id
        ))

        db.commit()

        cursor.close()

        return redirect(url_for("admin_students"))

    # =========================
    # بيانات الطالب
    # =========================

    cursor.execute("""
        SELECT
            id,
            fullName,
            phone,
            password,
            student_code,
            parent_phone,
            halaqa,
            level,
            memorized,
            remaining,
            teacher_id
        FROM users
        WHERE id = %s
        AND role = 'student'
    """, (student_id,))

    student = cursor.fetchone()

    # =========================
    # المعلمين
    # =========================

    cursor.execute("""
        SELECT
            id,
            fullName
        FROM users
        WHERE role = 'teacher'
        ORDER BY fullName
    """)

    teachers = cursor.fetchall()

    cursor.close()

    if not student:
        return "الطالب غير موجود"

    return render_template(
        "edit_student.html",
        student=student,
        teachers=teachers
    )


@app.route("/admin/students/delete/<int:student_id>", methods=["POST"])
def delete_student(student_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor()

    sql = """
        DELETE FROM users
        WHERE id = %s
        AND role = 'student'
    """

    cursor.execute(sql, (student_id,))

    db.commit()
    cursor.close()

    return redirect(url_for("admin_students"))

@app.route("/admin/teachers")
def admin_teachers():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    return render_template("admin_teachers.html")

@app.route("/api/admin/teachers", methods=["GET"])
def get_teachers():

    if "user_id" not in session:
        return jsonify({"message": "يجب تسجيل الدخول أولاً"}), 401

    if session["role"] != "admin":
        return jsonify({"message": "ليس لديك صلاحية"}), 403

    cursor = db.cursor(dictionary=True)

    sql = """
        SELECT
        id,
        fullName,
        phone,
        age,
        qualification,
        specialization,
        quran_experience,
        ijazah,
        notes
    FROM users
    WHERE role = 'teacher'
    ORDER BY id DESC
    """

    cursor.execute(sql)

    teachers = cursor.fetchall()

    cursor.close()

    return jsonify(teachers)

@app.route("/admin/teachers/add", methods=["GET", "POST"])
def add_teacher():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    if request.method == "POST":

        fullName = request.form.get("fullName")
        phone = request.form.get("phone")
        password = request.form.get("password")
        phone_pattern = r"^01[0-9]{9}$"

        if not re.fullmatch(phone_pattern, phone or ""):
            return "رقم هاتف المعلم غير صحيح"

        age = request.form.get("age") or None
        qualification = request.form.get("qualification")
        specialization = request.form.get("specialization")
        quran_experience = request.form.get("quran_experience") or None
        ijazah = request.form.get("ijazah")
        notes = request.form.get("notes")

        cursor = db.cursor()

        sql = """
            INSERT INTO users
            (
                fullName,
                phone,
                password,
                role,
                age,
                qualification,
                specialization,
                quran_experience,
                ijazah,
                notes
            )
            VALUES
            (
                %s,
                %s,
                %s,
                'teacher',
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
        """

        cursor.execute(sql, (
            fullName,
            phone,
            password,
            age,
            qualification,
            specialization,
            quran_experience,
            ijazah,
            notes
        ))

        db.commit()
        cursor.close()

        return redirect(url_for("admin_teachers"))

    return render_template("add_teacher.html")
 
@app.route("/admin/teachers/edit/<int:teacher_id>", methods=["GET", "POST"])
def edit_teacher(teacher_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # =========================
    # تعديل بيانات المعلم
    # =========================

    if request.method == "POST":

        fullName = request.form.get("fullName")
        phone = request.form.get("phone")
        password = request.form.get("password")
        phone_pattern = r"^01[0-9]{9}$"

        if not re.fullmatch(phone_pattern, phone or ""):
            return "رقم هاتف المعلم غير صحيح"

        age = request.form.get("age") or None
        qualification = request.form.get("qualification")
        specialization = request.form.get("specialization")
        quran_experience = request.form.get("quran_experience") or None
        ijazah = request.form.get("ijazah")
        notes = request.form.get("notes")

        sql = """
            UPDATE users
            SET
                fullName = %s,
                phone = %s,
                password = %s,
                age = %s,
                qualification = %s,
                specialization = %s,
                quran_experience = %s,
                ijazah = %s,
                notes = %s
            WHERE id = %s
            AND role = 'teacher'
        """

        cursor.execute(sql, (
            fullName,
            phone,
            password,
            age,
            qualification,
            specialization,
            quran_experience,
            ijazah,
            notes,
            teacher_id
        ))

        db.commit()
        cursor.close()

        return redirect(url_for("admin_teachers"))

    # =========================
    # جلب بيانات المعلم
    # =========================

    sql = """
        SELECT
            id,
            fullName,
            phone,
            password,
            age,
            qualification,
            specialization,
            quran_experience,
            ijazah,
            notes
        FROM users
        WHERE id = %s
        AND role = 'teacher'
    """

    cursor.execute(sql, (teacher_id,))
    teacher = cursor.fetchone()

    cursor.close()

    if not teacher:
        return "المعلم غير موجود"

    return render_template(
        "edit_teacher.html",
        teacher=teacher
    )

@app.route("/admin/teachers/delete/<int:teacher_id>", methods=["POST"])
def delete_teacher(teacher_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor()

    sql = """
        DELETE FROM users
        WHERE id = %s
        AND role = 'teacher'
    """

    cursor.execute(sql, (teacher_id,))

    db.commit()

    cursor.close()

    return redirect(url_for("admin_teachers"))

@app.route("/api/questions", methods=["POST"]) 
def add_question(): 
 
    data = request.get_json() 
 
    question = data.get("question") 
 
 
    if not question: 
 
        return jsonify({ 
            "message": "برجاء كتابة السؤال أولاً" 
        }), 400 
 
 
    cursor = db.cursor() 
 
 
    sql = """ 
        INSERT INTO questions (question) 
        VALUES (%s) 
    """ 
 
 
    cursor.execute(sql, (question,)) 
 
    db.commit() 
 
    cursor.close() 
 
 
    return jsonify({ 
        "message": 
        "تم إرسال سؤالك بنجاح وسيتم الرد عليه قريباً!" 
    }) 
 

@app.route("/teacher/attendance", methods=["POST"])
def teacher_attendance():

    if "user_id" not in session:
        return jsonify({
            "message": "يجب تسجيل الدخول أولاً"
        }), 401

    if session["role"] != "teacher":
        return jsonify({
            "message": "ليس لديك صلاحية"
        }), 403

    data = request.get_json()

    student_id = data.get("student_id")
    status = data.get("status")

    if not student_id:
        return jsonify({
            "message": "لم يتم تحديد الطالب"
        }), 400

    if status not in ["present", "absent"]:
        return jsonify({
            "message": "حالة الحضور غير صحيحة"
        }), 400

    cursor = db.cursor(dictionary=True)

    # التأكد أن الطالب تابع لهذا المعلم
    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = %s
        AND role = 'student'
        AND teacher_id = %s
    """, (student_id, session["user_id"]))

    student = cursor.fetchone()

    if not student:
        cursor.close()

        return jsonify({
            "message": "هذا الطالب غير تابع لك"
        }), 403

    # هل يوجد تسجيل حضور لهذا الطالب اليوم؟
    cursor.execute("""
        SELECT id
        FROM attendance
        WHERE student_id = %s
        AND attendance_date = CURDATE()
    """, (student_id,))

    existing = cursor.fetchone()

    if existing:

        # لو موجود نغير الحالة
        cursor.execute("""
            UPDATE attendance
            SET status = %s,
                teacher_id = %s
            WHERE id = %s
        """, (
            status,
            session["user_id"],
            existing["id"]
        ))

    else:

        # تسجيل حضور جديد
        cursor.execute("""
            INSERT INTO attendance
            (
                student_id,
                teacher_id,
                attendance_date,
                status
            )
            VALUES
            (
                %s,
                %s,
                CURDATE(),
                %s
            )
        """, (
            student_id,
            session["user_id"],
            status
        ))

    db.commit()
    cursor.close()

    return jsonify({
        "message": "تم تسجيل الحضور بنجاح"
    })


@app.route("/teacher/attendance/<int:student_id>")
def student_attendance(student_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # التأكد أن الطالب تابع للمعلم الحالي
    cursor.execute("""
        SELECT id, fullName, student_code
        FROM users
        WHERE id = %s
        AND role = 'student'
        AND teacher_id = %s
    """, (student_id, session["user_id"]))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        return "هذا الطالب غير تابع لك"

    # جلب سجل الحضور
    cursor.execute("""
        SELECT
            attendance_date,
            status,
            notes
        FROM attendance
        WHERE student_id = %s
        ORDER BY attendance_date DESC
    """, (student_id,))

    attendance_records = cursor.fetchall()

    cursor.close()

    return render_template(
        "student_attendance.html",
        student=student,
        attendance_records=attendance_records
    )

@app.route("/teacher/tasmee3/<int:student_id>")
def student_tasmee3(student_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # التأكد أن الطالب تابع للمعلم الحالي
    cursor.execute("""
        SELECT
            id,
            fullName,
            student_code
        FROM users
        WHERE id = %s
        AND role = 'student'
        AND teacher_id = %s
    """, (student_id, session["user_id"]))

    student = cursor.fetchone()

    cursor.close()

    if not student:
        return "هذا الطالب غير تابع لك"

    return render_template(
        "student_tasmee3.html",
        student=student
    )

@app.route("/teacher/tasmee3/history/<int:student_id>")
def tasmee3_history(student_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # التأكد أن الطالب تابع للمعلم الحالي
    cursor.execute("""
        SELECT
            id,
            fullName,
            student_code
        FROM users
        WHERE id = %s
        AND role = 'student'
        AND teacher_id = %s
    """, (student_id, session["user_id"]))

    student = cursor.fetchone()

    if not student:
        cursor.close()
        return "هذا الطالب غير تابع لك"

    # جلب سجل التسميع
    cursor.execute("""
        SELECT
            id,
            date,
            surah,
            from_ayah,
            to_ayah,
            type,
            evaluation,
            notes
        FROM tasmee3
        WHERE student_id = %s
        AND teacher_id = %s
        ORDER BY date DESC, id DESC
    """, (student_id, session["user_id"]))

    tasmee3_records = cursor.fetchall()

    cursor.close()

    return render_template(
        "tasmee3_history.html",
        student=student,
        tasmee3_records=tasmee3_records
    )

@app.route("/teacher/tasmee3/edit/<int:tasmee3_id>", methods=["GET", "POST"])
def edit_tasmee3(tasmee3_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    if request.method == "POST":

        surah = request.form.get("surah")
        from_ayah = request.form.get("from_ayah") or None
        to_ayah = request.form.get("to_ayah") or None
        tasmee3_type = request.form.get("type") or None
        evaluation = request.form.get("evaluation") or None
        notes = request.form.get("notes") or None

        cursor.execute("""
            UPDATE tasmee3
            SET
                surah = %s,
                from_ayah = %s,
                to_ayah = %s,
                type = %s,
                evaluation = %s,
                notes = %s
            WHERE id = %s
            AND teacher_id = %s
        """, (
            surah,
            from_ayah,
            to_ayah,
            tasmee3_type,
            evaluation,
            notes,
            tasmee3_id,
            session["user_id"]
        ))

        db.commit()

        cursor.close()

        return redirect(
            url_for(
                "tasmee3_history",
                student_id=request.form.get("student_id")
            )
        )

    cursor.execute("""
        SELECT
            id,
            student_id,
            date,
            surah,
            from_ayah,
            to_ayah,
            type,
            evaluation,
            notes
        FROM tasmee3
        WHERE id = %s
        AND teacher_id = %s
    """, (tasmee3_id, session["user_id"]))

    record = cursor.fetchone()

    cursor.close()

    if not record:
        return "التسجيل غير موجود أو ليس لديك صلاحية لتعديله"

    return render_template(
        "edit_tasmee3.html",
        record=record
    )

@app.route("/teacher/tasmee3/delete/<int:tasmee3_id>", methods=["POST"])
def delete_tasmee3(tasmee3_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "teacher":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT student_id
        FROM tasmee3
        WHERE id = %s
        AND teacher_id = %s
    """, (tasmee3_id, session["user_id"]))

    record = cursor.fetchone()

    if not record:
        cursor.close()
        return "التسجيل غير موجود أو ليس لديك صلاحية لحذفه"

    student_id = record["student_id"]

    cursor.execute("""
        DELETE FROM tasmee3
        WHERE id = %s
        AND teacher_id = %s
    """, (tasmee3_id, session["user_id"]))

    db.commit()

    cursor.close()

    return redirect(
        url_for(
            "tasmee3_history",
            student_id=student_id
        )
    )

@app.route("/teacher/tasmee3", methods=["POST"])
def add_tasmee3():

    if "user_id" not in session:
        return jsonify({
            "message": "يجب تسجيل الدخول أولاً"
        }), 401

    if session["role"] != "teacher":
        return jsonify({
            "message": "ليس لديك صلاحية"
        }), 403

    data = request.get_json()

    student_id = data.get("student_id")
    surah = data.get("surah")
    from_ayah = data.get("from_ayah") or None
    to_ayah = data.get("to_ayah") or None
    tasmee3_type = data.get("type") or None
    evaluation = data.get("evaluation") or None
    notes = data.get("notes") or None

    if not student_id:
        return jsonify({
            "message": "لم يتم تحديد الطالب"
        }), 400

    if not surah:
        return jsonify({
            "message": "يجب اختيار السورة"
        }), 400

    cursor = db.cursor(dictionary=True)

    # التأكد أن الطالب تابع لهذا المعلم
    cursor.execute("""
        SELECT id
        FROM users
        WHERE id = %s
        AND role = 'student'
        AND teacher_id = %s
    """, (student_id, session["user_id"]))

    student = cursor.fetchone()

    if not student:
        cursor.close()

        return jsonify({
            "message": "هذا الطالب غير تابع لك"
        }), 403

    # تسجيل التسميع
    cursor.execute("""
        INSERT INTO tasmee3
        (
            student_id,
            teacher_id,
            date,
            surah,
            from_ayah,
            to_ayah,
            type,
            evaluation,
            notes
        )
        VALUES
        (
            %s,
            %s,
            CURDATE(),
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        student_id,
        session["user_id"],
        surah,
        from_ayah,
        to_ayah,
        tasmee3_type,
        evaluation,
        notes
    ))

    db.commit()
    cursor.close()

    return jsonify({
        "message": "تم تسجيل التسميع بنجاح"
    })

 
@app.route("/api/questions", methods=["GET"]) 
def get_questions(): 
 
    cursor = db.cursor(dictionary=True) 
 
 
    sql = """ 
        SELECT 
            id, 
            question, 
            answer, 
            created_at 
        FROM questions 
        ORDER BY created_at DESC 
    """ 
 
 
    cursor.execute(sql) 
 
    questions = cursor.fetchall() 
 
    cursor.close() 
 
 
    return jsonify(questions) 
 
 
@app.route("/api/admin/pending-questions", methods=["GET"]) 
def pending_questions(): 
 
    cursor = db.cursor(dictionary=True) 
 
 
    sql = """ 
        SELECT 
            id, 
            question, 
            answer, 
            created_at 
        FROM questions 
        WHERE answer IS NULL 
        ORDER BY created_at DESC 
    """ 
 
 
    cursor.execute(sql) 
 
    questions = cursor.fetchall() 
 
    cursor.close() 
 
 
    return jsonify(questions) 
 
 
@app.route("/api/admin/answer-question", methods=["POST"]) 
def answer_question(): 
 
    data = request.get_json() 
 
 
    question_id = data.get("id") 
    answer = data.get("answer") 
 
 
    if not question_id or not answer: 
 
        return jsonify({ 
            "message": "البيانات غير مكتملة" 
        }), 400 
 
 
    cursor = db.cursor() 
 
 
    sql = """ 
        UPDATE questions 
        SET answer = %s 
        WHERE id = %s 
    """ 
 
 
    cursor.execute( 
        sql, 
        (answer, question_id) 
    ) 
 
 
    db.commit() 
 
    cursor.close() 
 
 
    return jsonify({ 
        "message": "تم حفظ الإجابة بنجاح!" 
    }) 
 

# =========================
# Admin - Halaqat
# =========================

@app.route("/admin/halaqat")
def admin_halaqat():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    # جلب الحلقات مع اسم المدرس
    cursor.execute("""
        SELECT
            halaqat.id,
            halaqat.name,
            halaqat.type,
            halaqat.teacher_id,
            halaqat.days,
            halaqat.time,
            halaqat.notes,
            users.fullName AS teacher_name
        FROM halaqat
        LEFT JOIN users
            ON halaqat.teacher_id = users.id
            AND users.role = 'teacher'
        ORDER BY halaqat.id DESC
    """)

    halaqat = cursor.fetchall()

    # جلب المدرسين لاستخدامهم في الإضافة والتعديل
    cursor.execute("""
        SELECT
            id,
            fullName
        FROM users
        WHERE role = 'teacher'
        ORDER BY fullName
    """)

    teachers = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_halaqat.html",
        halaqat=halaqat,
        teachers=teachers
    )


@app.route("/admin/halaqat/add", methods=["POST"])
def add_halaqa():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    name = request.form.get("name")
    halaqa_type = request.form.get("type")
    teacher_id = request.form.get("teacher_id") or None
    days = request.form.get("days")
    time = request.form.get("time")
    notes = request.form.get("notes")

    if not name:
        return "يجب إدخال اسم الحلقة"

    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO halaqat
        (
            name,
            type,
            teacher_id,
            days,
            time,
            notes
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
    """, (
        name,
        halaqa_type,
        teacher_id,
        days,
        time,
        notes
    ))

    db.commit()
    cursor.close()

    return redirect(url_for("admin_halaqat"))


@app.route("/admin/halaqat/delete/<int:halaqa_id>", methods=["POST"])
def delete_halaqa(halaqa_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM halaqat
        WHERE id = %s
    """, (halaqa_id,))

    db.commit()
    cursor.close()

    return redirect(url_for("admin_halaqat"))


# =========================
# Admin - Attendance
# =========================

@app.route("/admin/attendance")
def admin_attendance():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            attendance.id,
            attendance.attendance_date,
            attendance.status,
            attendance.notes,

            students.fullName AS student_name,
            students.student_code,

            teachers.fullName AS teacher_name

        FROM attendance

        JOIN users AS students
            ON attendance.student_id = students.id

        LEFT JOIN users AS teachers
            ON attendance.teacher_id = teachers.id
            AND teachers.role = 'teacher'

        ORDER BY
            attendance.attendance_date DESC,
            attendance.id DESC
    """)

    attendance_records = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_attendance.html",
        attendance_records=attendance_records
    )

 
@app.route("/admin/tasmee3")
def admin_tasmee3():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            tasmee3.id,
            tasmee3.date,
            tasmee3.surah,
            tasmee3.from_ayah,
            tasmee3.to_ayah,
            tasmee3.type,
            tasmee3.evaluation,
            tasmee3.notes,
            students.fullName AS student_name,
            students.student_code,
            teachers.fullName AS teacher_name
        FROM tasmee3
        JOIN users AS students
            ON tasmee3.student_id = students.id
        LEFT JOIN users AS teachers
            ON tasmee3.teacher_id = teachers.id
            AND teachers.role = 'teacher'
        ORDER BY tasmee3.date DESC, tasmee3.id DESC
    """)

    tasmee3_records = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_tasmee3.html",
        tasmee3_records=tasmee3_records
    )


@app.route("/admin/levels")
def admin_levels():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if session["role"] != "admin":
        return "ليس لديك صلاحية للوصول إلى هذه الصفحة"

    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            students.id,
            students.fullName,
            students.student_code,
            students.halaqa,
            students.level,
            students.memorized,
            students.remaining,
            teachers.fullName AS teacher_name
        FROM users AS students
        LEFT JOIN users AS teachers
            ON students.teacher_id = teachers.id
            AND teachers.role = 'teacher'
        WHERE students.role = 'student'
        ORDER BY students.fullName
    """)

    students = cursor.fetchall()

    cursor.close()

    return render_template(
        "admin_levels.html",
        students=students
    )


if __name__ == "__main__": 
 
    app.run(debug=True) 
 