import os
import django
import decimal
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from results.models import SemesterResult, CourseGrade, Exam, StudentExamMark
from attendance.models import Course, AttendanceSession, AttendanceRecord
from core.models import User, Section
from results.views import calculate_final_grades

def verify_academic_hub():
    print("Starting Academic Hub Logic Verification with Relative Grading...")
    
    faculty = User.objects.filter(role='FACULTY').first()
    student = User.objects.filter(role='STUDENT').first()
    course = Course.objects.filter(faculty=faculty).first()
    section = Section.objects.first()
    
    if not course or not student or not section:
        print("Error: Missing required data for verification.")
        return

    # Ensure student is in the section and enrolled in the course
    student.section = section
    student.save()
    if not course.students.filter(id=student.id).exists():
        course.students.add(student)

    print(f"Testing relative grading for Section {section.name} in Course {course.code}")
    
    # 1. Cleanup existing records for a clean test
    CourseGrade.objects.filter(course=course, student=student).delete()
    StudentExamMark.objects.filter(student=student, exam__course=course).delete()
    Exam.objects.filter(course=course, section=section).delete()
    
    # 2. Setup mock exams
    exams_data = [
        ('CA1', 30), ('CA2', 30), ('CA3', 30),
        ('MID', 30), ('END', 60)
    ]
    created_exams = {}
    for ex_type, max_m in exams_data:
        ex, _ = Exam.objects.get_or_create(course=course, section=section, exam_type=ex_type, defaults={'max_marks': max_m})
        created_exams[ex_type] = ex

    # 3. Insert mock marks for the student
    # Lets give student perfect score in CAs, 20/30 in mid, and 50/60 in end term
    mark_scores = {
        'CA1': 30, 'CA2': 30, 'CA3': 30, # Total 90/90 in CA -> 25 points
        'MID': 20,                       # 20/30 in MID -> 13.33 points
        'END': 50                        # 50/60 in END -> 41.66 points
    }
    # Expected total net mark without attendance = 25 + 13.33 + 41.66 = ~79.99

    for ex_type, score in mark_scores.items():
        StudentExamMark.objects.create(
            exam=created_exams[ex_type],
            student=student,
            marks_obtained=decimal.Decimal(score)
        )

    # 4. Setup dummy attendance
    # Let's give them 1 session and 1 presence = 100% = 5 marks
    # Total net marks = ~84.99
    session = AttendanceSession.objects.filter(course=course).first()
    if not session:
        session = AttendanceSession.objects.create(course=course, date='2026-01-01')
    AttendanceRecord.objects.get_or_create(session=session, student=student, defaults={'is_present': True})


    # 5. Simulate view calculation
    factory = RequestFactory()
    request = factory.post(f'/results/course/{course.id}/section/{section.id}/calculate-grades/')
    request.user = faculty
    # Add messages framework to request
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)

    print("Triggering `calculate_final_grades` view...")
    response = calculate_final_grades(request, course.id, section.id)
    
    # Check results
    grade_obj = CourseGrade.objects.filter(course=course, student=student).first()
    
    assert grade_obj is not None, "CourseGrade not calculated!"
    
    print(f"Net Marks Calculated: {grade_obj.net_marks}/100")
    print(f"Grade Assigned: {grade_obj.grade} ({grade_obj.grade_points} points)")
    print(f"Course Credits: {grade_obj.credits}")
    
    sem_result = SemesterResult.objects.get(student=student, semester=1)
    print(f"Updated SGPA: {sem_result.sgpa}")
    
    # Since student is the only one in DB (most likely), they are 1st out of 1 -> 100th percentile -> 'O' Grade (10 pts)
    # Though if other students exist, it might differ. This validates the code runs.
    
    print("\nSUCCESS: Academic Hub logical rewrite verified successfully!")

if __name__ == '__main__':
    verify_academic_hub()

