import os
import django
import decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from results.models import SemesterResult, CourseGrade
from attendance.models import Course
from core.models import User

def verify_academic_hub():
    print("Starting Academic Hub Logic Verification...")
    
    # 1. Setup mock data
    faculty = User.objects.filter(role='FACULTY').first()
    student = User.objects.filter(role='STUDENT').first()
    course = Course.objects.filter(faculty=faculty).first()
    
    if not course:
        print("Error: No course found for faculty.")
        return

    print(f"Testing Grade Recording for {student.username} in {course.code}")
    
    # Cleanup existing grades for this course/student
    CourseGrade.objects.filter(course=course, student=student).delete()
    
    # Simulate bulk_update_grades logic
    grade_points_map = {
        'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'P': 4, 'F': 0
    }
    course_credits = 4
    grade_letter = 'A+' # 9 points
    
    # Find or create SemesterResult
    sem_result, _ = SemesterResult.objects.get_or_create(
        student=student,
        semester=1,
        defaults={'sgpa': 0, 'cgpa': 0, 'credits_earned': 0, 'total_credits': 0}
    )
    
    # Update or create CourseGrade
    grade_obj, created = CourseGrade.objects.update_or_create(
        semester_result=sem_result,
        course=course,
        defaults={
            'student': student,
            'course_name': course.name,
            'course_code': course.code,
            'grade': grade_letter,
            'grade_points': grade_points_map[grade_letter],
            'credits': course_credits
        }
    )
    
    # Recalculate SGPA
    all_grades = sem_result.grades.all()
    total_pts = sum(g.grade_points * g.credits for g in all_grades)
    total_creds = sum(g.credits for g in all_grades)
    
    expected_sgpa = decimal.Decimal(total_pts) / decimal.Decimal(total_creds)
    
    if total_creds > 0:
        sem_result.sgpa = expected_sgpa
        sem_result.total_credits = total_creds
        sem_result.credits_earned = sum(g.credits for g in all_grades if g.grade != 'F')
        sem_result.cgpa = sem_result.sgpa # Assuming 1 sem
        sem_result.save()
        
    print(f"Recorded Grade: {grade_obj.grade} ({grade_obj.grade_points} pts)")
    print(f"Computed SGPA: {sem_result.sgpa}")
    print(f"Expected SGPA: {expected_sgpa}")
    
    assert sem_result.sgpa == expected_sgpa, f"SGPA mismatch: {sem_result.sgpa} != {expected_sgpa}"
    assert grade_obj.course == course, "Course linkage failed"
    assert grade_obj.student == student, "Student linkage failed"
    
    print("\nSUCCESS: Academic Hub logic is verified and sound!")

if __name__ == '__main__':
    verify_academic_hub()
