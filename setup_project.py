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
from remedial_classes.models import RemedialSession
from food_ordering.models import FoodItem, TimeSlot, OrderGroup, OrderItem
from results.models import SemesterResult, CourseGrade, Exam as ResultExam, StudentExamMark
from exams.models import Exam
from django.core.files.base import ContentFile
from resource_management.models import CampusBlock, Classroom
from admissions.models import AdmissionApplication, AdmissionQuery

def generate_uid(role):
    if role == 'STUDENT':
        return '123' + ''.join(random.choices(string.digits, k=5))
    elif role == 'FACULTY':
        return ''.join(random.choices(string.digits, k=4))
    return None

import shutil

class RoomBooker:
    """Manages classroom and faculty availability to avoid clashes."""
    def __init__(self):
        # (day_of_week/date, slot_number) -> set of classroom_ids
        self.occupied_rooms = {}
        # (day_of_week/date, slot_number) -> set of faculty_ids
        self.occupied_faculty = {}

    def is_available(self, when, slot, classroom=None, faculty=None):
        key = (when, slot)
        if classroom:
            if classroom.id in self.occupied_rooms.get(key, set()):
                return False
        if faculty:
            if faculty.id in self.occupied_faculty.get(key, set()):
                return False
        return True

    def book(self, when, slot, classroom=None, faculty=None):
        key = (when, slot)
        if classroom:
            if key not in self.occupied_rooms:
                self.occupied_rooms[key] = set()
            self.occupied_rooms[key].add(classroom.id)
        if faculty:
            if key not in self.occupied_faculty:
                self.occupied_faculty[key] = set()
            self.occupied_faculty[key].add(faculty.id)

def setup_project():
    print("Flushing existing data...")
    
    exam_media_path = os.path.join(settings.MEDIA_ROOT, 'exams')
    if os.path.exists(exam_media_path):
        shutil.rmtree(exam_media_path)
        print(f"Cleared existing exam media at {exam_media_path}")

    # Delete all relevant models
    User.objects.all().delete()
    Section.objects.all().delete()
    Course.objects.all().delete()
    FoodItem.objects.all().delete()
    TimeSlot.objects.all().delete()
    TimetableSlot.objects.all().delete()
    AttendanceSession.objects.all().delete()
    RemedialSession.objects.all().delete()
    Exam.objects.all().delete()
    SemesterResult.objects.all().delete()
    CampusBlock.objects.all().delete()
    Classroom.objects.all().delete()
    AdmissionApplication.objects.all().delete()
    AdmissionQuery.objects.all().delete()

    print("0. Creating Admin Superuser...")
    admin = User.objects.create_superuser(
        username='admin', email='admin@lpu.in', password='admin', role='ADMIN'
    )
    admin.is_approved = True
    admin.save()

    print("1. Creating Campus Infrastructure (10 Blocks, 900 Classrooms)...")
    blocks = [CampusBlock(name=f"Block {i}", description=f"Academic Block {i}") for i in range(1, 11)]
    CampusBlock.objects.bulk_create(blocks)
    
    saved_blocks = CampusBlock.objects.all().order_by('id')
    classrooms_to_create = []
    for block in saved_blocks:
        block_num = int(block.name.split()[1])
        for floor in range(1, 10):
            for room in range(1, 11):
                room_txt = f"{floor}{room:02d}"
                room_number = f"{block_num}-{room_txt}"
                classrooms_to_create.append(Classroom(
                    block=block, room_number=room_number, capacity=60, room_type='CLASSROOM'
                ))
    Classroom.objects.bulk_create(classrooms_to_create)
    all_classrooms = list(Classroom.objects.all())
    print(f"Created {len(classrooms_to_create)} classrooms.")
    
    print("2. Creating Sections...")
    sections = [Section.objects.create(name=name) for name in ['K23RT', 'K23PT', 'K23HG']]

    print("3. Creating 5 Faculties...")
    faculties = []
    for name in ["Gauth", "Sandhya", "Ramesh", "Kavita", "Suresh"]:
        faculty = User.objects.create_user(
            username=name, email=f'{name.lower()}@lpu.in', password='123',
            role='FACULTY', is_approved=True, is_active=True
        )
        faculty.uid = generate_uid('FACULTY')
        faculty.save()
        faculties.append(faculty)

    print("4. Creating 30 Students...")
    for i, name in enumerate([
        "Aarav", "Ishani", "Vihaan", "Advika", "Reyansh", "Myra", "Siddharth", "Ananya", "Kabir", "Zara",
        "Rohan", "Sanya", "Arjun", "Kritika", "Dhruv", "Riya", "Aryan", "Pooja", "Kartik", "Sneha",
        "Aditya", "Tanvi", "Pranav", "Ishita", "Rahul", "Mehak", "Dev", "Kyra", "Yash", "Avni"
    ]):
        student = User.objects.create_user(
            username=name, email=f'{name.lower()}@lpu.in', password='123',
            role='STUDENT', section=sections[i // 10], is_approved=True, is_active=True
        )
        student.uid = generate_uid('STUDENT')
        while User.objects.filter(uid=student.uid).exclude(id=student.id).exists():
            student.uid = generate_uid('STUDENT')
        student.save()
    students = list(User.objects.filter(role='STUDENT'))

    print("5. Creating 5 Current Courses...")
    courses = []
    current_course_data = [
        ("Artificial Intelligence", "CSE401"), ("Mobile App Development", "CSE402"),
        ("Cyber Security", "CSE403"), ("Natural Language Processing", "CSE404"), ("Embedded Systems", "ECE405")
    ]
    for i, (name, code) in enumerate(current_course_data):
        course = Course.objects.create(name=name, code=code, faculty=faculties[i])
        course.students.set(students)
        courses.append(course)

    print("6. Generating Timetable with Clash Detection...")
    booker = RoomBooker()
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    for section in sections:
        course_slots_count = {course.id: 0 for course in courses}
        for day in days:
            slots_filled = 0
            possible_slots = list(range(1, 8))
            random.shuffle(possible_slots)
            for slot_num in possible_slots:
                if slots_filled >= 4: break
                shuffled_courses = [c for c in courses if course_slots_count[c.id] < 4]
                random.shuffle(shuffled_courses)
                for course in shuffled_courses:
                    for _ in range(20): # More attempts for room
                        room = random.choice(all_classrooms)
                        if booker.is_available(day, slot_num, classroom=room, faculty=course.faculty):
                            TimetableSlot.objects.create(
                                day_of_week=day, slot_number=slot_num,
                                course=course, section=section, classroom=room
                            )
                            booker.book(day, slot_num, classroom=room, faculty=course.faculty)
                            course_slots_count[course.id] += 1
                            slots_filled += 1
                            break
                    if slots_filled > 0: break

    print("7. Creating Attendance Data...")
    today = timezone.now().date()
    for course in courses:
        for d in range(1, 4):
            session_date = today - timedelta(days=d)
            for section in sections:
                slot = TimetableSlot.objects.filter(course=course, section=section).first()
                if slot:
                    session = AttendanceSession.objects.create(course=course, date=session_date, slot=slot)
                    for student in [s for s in students if s.section == section]:
                        AttendanceRecord.objects.create(session=session, student=student, is_present=random.random() > 0.15)

    print("8. Creating Food Items & Time Slots...")
    food_data = [
        ("Samosa", 15.0), ("Veg Burger", 45.0), ("Cold Coffee", 50.0), 
        ("Masala Dosa", 60.0), ("Paneer Wrap", 75.0), ("Iced Tea", 35.0)
    ]
    for name, price in food_data:
        FoodItem.objects.create(name=name, price=price, description=f"Fresh {name}")
    for start, end in [("10:00", "11:00"), ("12:00", "13:00"), ("14:00", "15:00")]:
        TimeSlot.objects.create(start_time=f"{start}:00", end_time=f"{end}:00")

    print("9. Creating Exams with Strict Room Assignment...")
    for course in courses:
        # Pick a unique Saturday and unique room
        exam_date = today + timedelta(days=(5 - today.weekday() + 7) % 7 + 14)
        # Use slot 1 for all exams for now, but different rooms
        for room in all_classrooms:
            if booker.is_available(exam_date, 1, classroom=room, faculty=course.faculty):
                exam = Exam.objects.create(
                    course=course, exam_type=random.choice(['MID', 'END', 'CA']),
                    date=timezone.make_aware(timezone.datetime.combine(exam_date, timezone.datetime.min.time())),
                    classroom=room
                )
                booker.book(exam_date, 1, classroom=room, faculty=course.faculty)
                break

    print("10. Creating Historical Results...")
    pass

    print("11. Creating Admissions Data & Remedials...")
    # Admissions
    for i in range(5):
        AdmissionApplication.objects.create(
            student_name=f"Applicant {i}", email=f"app{i}@gmail.com", 
            phone=f"987654321{i}", course_applied="B.Tech CSE"
        )
        AdmissionQuery.objects.create(
            name=f"Inquirer {i}", email=f"inq{i}@gmail.com",
            subject="Fee Structure", message="What are the annual fees?"
        )
    
    # Remedials
    for _ in range(3):
        course = random.choice(courses)
        day = random.choice(days)
        slot = random.randint(1, 7)
        for room in all_classrooms:
            if booker.is_available(day, slot, classroom=room, faculty=course.faculty):
                RemedialSession.objects.create(
                    course=course, faculty=course.faculty, date=today + timedelta(days=5),
                    slot_number=slot, classroom=room, status='APPROVED'
                )
                booker.book(day, slot, classroom=room, faculty=course.faculty)
                break

    print("\nProject Setup & Mock Data Generation Complete!")

if __name__ == '__main__':
    setup_project()
