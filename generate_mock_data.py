import os
import django
import random
from datetime import timedelta
from django.utils import timezone
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from core.models import User
from attendance.models import Course, AttendanceSession, AttendanceRecord, AttendanceEditRequest
from remedial_classes.models import RemedialSession, RemedialAttendance
from food_ordering.models import FoodItem, TimeSlot, OrderGroup, OrderItem

def generate_mock_data():
    print("Flushing existing data (except admin)...")
    User.objects.exclude(username='admin').delete()
    Course.objects.all().delete()
    FoodItem.objects.all().delete()
    TimeSlot.objects.all().delete()

    print("Creating 10 Students...")
    student_names = ["Arjun", "Riya", "Mohammad", "Priya", "Rahul", "Ananya", "Karan", "Sneha", "Vikram", "Neha"]
    students = []
    for num, name in enumerate(student_names, start=1):
        student = User.objects.create_user(
            username=name,
            email=f'{name.lower()}@lpu.in',
            password='123',
            role='STUDENT',
            is_approved=True,
            is_active=True
        )
        students.append(student)

    print("Creating 5 Faculties...")
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
        faculties.append(faculty)

    print("Creating 5 Courses (1 per Faculty)...")
    course_names = ["Data Structures", "Web Development", "Machine Learning", "Cloud Computing", "Database Systems"]
    courses = []
    for i in range(5):
        course = Course.objects.create(
            name=course_names[i],
            code=f"CSE{301 + i}",
            faculty=faculties[i]
        )
        # Enroll all 10 students in all 5 courses
        course.students.set(students)
        courses.append(course)
        
    print("Creating Attendance Data (Past 3 days)...")
    today = timezone.now().date()
    for course in courses:
        for d in range(1, 4):
            session_date = today - timedelta(days=d)
            session = AttendanceSession.objects.create(course=course, date=session_date)
            session.created_at = timezone.now() - timedelta(days=d)
            session.save()
            
            for student in students:
                # Randomize presence 80% present
                is_present = random.random() > 0.2
                AttendanceRecord.objects.create(session=session, student=student, is_present=is_present)

    print("Creating Food Items & Time Slots...")
    food_data = [
        ("Samosa", 15.00, "food_items/samosa.png"), 
        ("Veg Burger", 45.00, "food_items/veg_burger.png"), 
        ("Cold Coffee", 50.00, "food_items/cold_coffee.png"), 
        ("Masala Dosa", 60.00, "food_items/masala_dosa.png"), 
        ("Paneer Wrap", 75.00, "food_items/paneer_wrap.png")
    ]
    for name, price, img in food_data:
        FoodItem.objects.create(name=name, price=price, description=f"Delicious {name}", image=img)
        
    slots = [("10:00", "11:00"), ("12:00", "13:00"), ("14:00", "15:00")]
    for start, end in slots:
        TimeSlot.objects.create(start_time=f"{start}:00", end_time=f"{end}:00")

    print("Creating 1 Pending Edit Request & 1 Make-Up Class for Admin view")
    # Edit Request
    first_session = AttendanceSession.objects.first()
    AttendanceEditRequest.objects.create(
        session=first_session,
        student=students[0],
        faculty=first_session.course.faculty,
        requested_is_present=True,
        reason="Marked absent by mistake. Has signed medical slip.",
        status='PENDING'
    )
    
    # Remedial Session
    RemedialSession.objects.create(
        course=courses[0],
        faculty=courses[0].faculty,
        date=today + timedelta(days=2),
        start_time="16:00:00",
        end_time="17:00:00",
        status='PENDING'
    )

    print("Creating Mock Exams & Dummy Files...")
    from exams.models import Exam
    from django.core.files.base import ContentFile
    
    # Ensure media directories exist
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'exams/syllabi'), exist_ok=True)
    os.makedirs(os.path.join(settings.MEDIA_ROOT, 'exams/resources'), exist_ok=True)
    
    dummy_syllabus = ContentFile("This is a mock syllabus for the course examination.")
    dummy_resource = ContentFile("This is a mock study resource/material for the examination.")
    
    exam_types = ['MID', 'END', 'CA']
    for i, course in enumerate(courses):
        # Generate a random time between 9 AM and 4 PM (16:00) to ensure it ends by 5 or 6 PM
        random_hour = random.randint(9, 16)
        random_minute = random.choice([0, 15, 30, 45])
        
        exam_date = timezone.now() + timedelta(days=random.randint(10, 30))
        exam_date = exam_date.replace(hour=random_hour, minute=random_minute, second=0, microsecond=0)
        
        exam = Exam.objects.create(
            course=course,
            exam_type=random.choice(exam_types),
            date=exam_date
        )
        exam.syllabus.save(f'syllabus_{course.code.lower()}.txt', dummy_syllabus)
        exam.resources.save(f'resource_{course.code.lower()}.txt', dummy_resource)

    print("Mock Data Generation Complete!")

if __name__ == '__main__':
    generate_mock_data()
