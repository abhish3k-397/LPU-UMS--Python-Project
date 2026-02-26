import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from results.models import CourseGrade, SemesterResult
from core.models import User
from attendance.models import Course

students = User.objects.filter(role='STUDENT')
fixes_made = 0
for student in students:
    # Find active courses
    active_course_ids = list(Course.objects.filter(students=student).values_list('id', flat=True))
    
    # Check if this student has any grades with course_id in active_course_ids lying in semester 1
    wrong_grades = CourseGrade.objects.filter(student=student, course_id__in=active_course_ids, semester_result__semester__lt=4)
    
    for g in wrong_grades:
        # Find proper semester
        # The student's highest semester from mock data is likely 3, so ongoing is 4.
        # Let's find highest semester where course is None (mock data)
        highest_mock_sem = SemesterResult.objects.filter(student=student, grades__course__isnull=True).order_by('-semester').first()
        target_sem = (highest_mock_sem.semester + 1) if highest_mock_sem else 1
        
        # Get or create the proper semester result
        correct_sr, _ = SemesterResult.objects.get_or_create(
            student=student, semester=target_sem,
            defaults={'sgpa': 0, 'cgpa': 0, 'credits_earned': 0, 'total_credits': 0}
        )
        
        # Move the grade
        print(f"Moving {g.course_code} for {student.username} from Sem {g.semester_result.semester} to Sem {correct_sr.semester}")
        g.semester_result = correct_sr
        g.save()
        fixes_made += 1

print(f"Moved {fixes_made} grades.")
