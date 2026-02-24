import os
import django
import random
import string
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from core.models import User, Section
from attendance.models import Course, AttendanceSession, AttendanceRecord, AttendanceEditRequest, TimetableSlot
from remedial_classes.models import RemedialSession, RemedialAttendance
from food_ordering.models import FoodItem, TimeSlot, OrderGroup, OrderItem
from results.models import SemesterResult, CourseGrade
from exams.models import Exam
from django.core.files.base import ContentFile

def generate_uid(role):
    if role == 'STUDENT':
        return '123' + ''.join(random.choices(string.digits, k=5))
    elif role == 'FACULTY':
        return ''.join(random.choices(string.digits, k=4))
    return None

import shutil

def setup_project():
    print("Flushing existing data...")
    
    # Clean up media files that get recreated
    exam_media_path = os.path.join(settings.MEDIA_ROOT, 'exams')
    if os.path.exists(exam_media_path):
        shutil.rmtree(exam_media_path)
        print(f"Cleared existing exam media at {exam_media_path}")

    User.objects.all().delete()
    Section.objects.all().delete()

    print("0. Creating Admin Superuser...")
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@lpu.in',
        password='admin',
        role='ADMIN'
    )
    admin.is_approved = True
    admin.save()
    Course.objects.all().delete()
    FoodItem.objects.all().delete()
    TimeSlot.objects.all().delete()
    TimetableSlot.objects.all().delete()
    AttendanceSession.objects.all().delete()
    RemedialSession.objects.all().delete()
    Exam.objects.all().delete()
    SemesterResult.objects.all().delete()

    print("1. Creating Sections...")
    section_names = ['K23RT', 'K23PT', 'K23HG']
    sections = [Section.objects.create(name=name) for name in section_names]

    print("2. Creating 5 Faculties...")
    faculty_names = ["Gauth", "Sandhya", "Ramesh", "Kavita", "Suresh"]
    faculties = []
    for name in faculty_names:
        faculty = User.objects.create_user(
            username=name,
            email=f'{name.lower()}@lpu.in',
            password='123',
            role='FACULTY',
            is_approved=True,
            is_active=True
        )
        faculty.uid = generate_uid('FACULTY')
        faculty.save()
        faculties.append(faculty)

    print("3. Creating 30 Students (10 per section)...")
    student_base_names = [
        "Aarav", "Ishani", "Vihaan", "Advika", "Reyansh", "Myra", "Siddharth", "Ananya", "Kabir", "Zara",
        "Rohan", "Sanya", "Arjun", "Kritika", "Dhruv", "Riya", "Aryan", "Pooja", "Kartik", "Sneha",
        "Aditya", "Tanvi", "Pranav", "Ishita", "Rahul", "Mehak", "Dev", "Kyra", "Yash", "Avni"
    ]
    students = []
    for i, name in enumerate(student_base_names):
        section = sections[i // 10]
        student = User.objects.create_user(
            username=name,
            email=f'{name.lower()}@lpu.in',
            password='123',
            role='STUDENT',
            section=section,
            is_approved=True,
            is_active=True
        )
        student.uid = generate_uid('STUDENT')
        # Collision check
        while User.objects.filter(uid=student.uid).exclude(id=student.id).exists():
            student.uid = generate_uid('STUDENT')
        student.save()
        students.append(student)

    print("4. Creating 5 Current Courses (Semester 4)...")
    current_course_data = [
        ("Artificial Intelligence", "CSE401"),
        ("Mobile App Development", "CSE402"),
        ("Cyber Security", "CSE403"),
        ("Natural Language Processing", "CSE404"),
        ("Embedded Systems", "ECE405")
    ]
    courses = []
    for i in range(5):
        name, code = current_course_data[i]
        course = Course.objects.create(
            name=name,
            code=code,
            faculty=faculties[i]
        )
        # Enroll all students in ALL courses for simplicity in this mock setup
        course.students.set(students)
        courses.append(course)

    print("5. Generating Timetable (60 slots total)...")
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    activity_map = {} # (day, slot_number) -> set of course_ids (to avoid faculty clashes)

    for section in sections:
        course_slots_count = {course.id: 0 for course in courses}
        for day in days:
            slots_for_today = 0
            for slot_num in range(1, 8):
                if slots_for_today >= 4: # Max 4 classes per day per section
                    continue
                
                shuffled_courses = courses[:]
                random.shuffle(shuffled_courses)
                for course in shuffled_courses:
                    if course_slots_count[course.id] < 4:
                        key = (day, slot_num)
                        if key not in activity_map:
                            activity_map[key] = set()
                        
                        if course.id not in activity_map[key]:
                            TimetableSlot.objects.create(
                                day_of_week=day,
                                slot_number=slot_num,
                                course=course,
                                section=section
                            )
                            activity_map[key].add(course.id)
                            course_slots_count[course.id] += 1
                            slots_for_today += 1
                            break

    print("6. Creating Attendance Data (Past 3 days)...")
    today = timezone.now().date()
    for course in courses:
        for d in range(1, 4):
            session_date = today - timedelta(days=d)
            # Find a slot for this course if it exists in timetable for a day
            # For simplicity, we create sessions regardless of slot existence here 
            # or we can link to an actual slot.
            slot = TimetableSlot.objects.filter(course=course).first() 
            session = AttendanceSession.objects.create(
                course=course, 
                date=session_date,
                slot=slot
            )
            
            for student in students:
                is_present = random.random() > 0.15 # 85% attendance
                AttendanceRecord.objects.create(session=session, student=student, is_present=is_present)

    print("7. Creating Food Items & Time Slots...")
    food_data = [
        ("Samosa", 15.00, "food_items/samosa.png"), 
        ("Veg Burger", 45.00, "food_items/veg_burger.png"), 
        ("Cold Coffee", 50.00, "food_items/cold_coffee.png"), 
        ("Masala Dosa", 60.00, "food_items/masala_dosa.png"), 
        ("Paneer Wrap", 75.00, "food_items/paneer_wrap.png"), 
        ("Iced Tea", 35.00, "food_items/iced_tea.png")
    ]
    for name, price, img_path in food_data:
        FoodItem.objects.create(
            name=name, 
            price=price, 
            description=f"Fresh {name}",
            image=img_path
        )
        
    f_slots = [("10:00", "11:00"), ("12:00", "13:00"), ("14:00", "15:00")]
    for start, end in f_slots:
        TimeSlot.objects.create(start_time=f"{start}:00", end_time=f"{end}:00")

    print("8. Creating Exams & Study Resources...")
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'exams/syllabi'), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'exams/resources'), exist_ok=True)
    
    exam_types = ['MID', 'END', 'CA']
    for course in courses:
        exam_date = timezone.now() + timedelta(days=random.randint(15, 45))
        exam = Exam.objects.create(
            course=course,
            exam_type=random.choice(exam_types),
            date=exam_date
        )
        # Dummy file saves
        exam.syllabus.save(f'syllabus_{course.code}.txt', ContentFile("Mock Syllabus Content"))
        exam.resources.save(f'resource_{course.code}.txt', ContentFile("Mock Resource Content"))

    print("9. Creating Historical Results (3 Semesters)...")
    sem_courses_pool = {
        1: [("Programming Fundamentals", "CSE101", 4), ("Mathematics-I", "MTH101", 4), ("English-I", "ENG101", 2)],
        2: [("Data Structures", "CSE201", 4), ("Physics", "PHY101", 4), ("Logic Design", "ECE201", 3)],
        3: [("Operating Systems", "CSE301", 4), ("DBMS", "CSE303", 4), ("Discrete Math", "MTH301", 4)]
    }
    grades_map = {'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'P': 4}

    for student in students:
        total_points = 0
        total_credits = 0
        for sem in range(1, 4):
            s_courses = sem_courses_pool[sem]
            s_credits = sum(c[2] for c in s_courses)
            s_points = 0
            
            # Create a list of grades first to calculate SGPA
            grades_to_create = []
            for c_name, c_code, c_credits in s_courses:
                grade = random.choice(list(grades_map.keys()))
                g_p = grades_map[grade]
                grades_to_create.append({
                    'name': c_name, 'code': c_code, 'grade': grade, 'points': g_p, 'credits': c_credits
                })
                s_points += (g_p * c_credits)
            
            sgpa = round(s_points / s_credits, 2)
            total_points += s_points
            total_credits += s_credits
            cgpa = round(total_points / total_credits, 2)

            res = SemesterResult.objects.create(
                student=student, semester=sem, credits_earned=s_credits, total_credits=s_credits,
                sgpa=sgpa, cgpa=cgpa
            )
            
            for g in grades_to_create:
                CourseGrade.objects.create(
                    semester_result=res, course_name=g['name'], course_code=g['code'],
                    grade=g['grade'], grade_points=g['points'], credits=g['credits']
                )

    print("10. Creating Sample Requests...")
    # Attendance Edit Request
    sess = AttendanceSession.objects.first()
    AttendanceEditRequest.objects.create(
        session=sess, student=students[0], faculty=sess.course.faculty,
        requested_is_present=True, reason="Medical reasons", status='PENDING'
    )
    # Remedial Session
    RemedialSession.objects.create(
        course=courses[0], faculty=courses[0].faculty, date=today + timedelta(days=5),
        start_time="17:00:00", end_time="18:00:00", status='PENDING'
    )

    print("\nProject Setup & Mock Data Generation Complete!")
    print(f"Users created: {User.objects.count()} (including admin)")
    print(f"Timetable slots: {TimetableSlot.objects.count()}")

if __name__ == '__main__':
    setup_project()
