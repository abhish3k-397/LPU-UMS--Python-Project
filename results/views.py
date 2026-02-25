from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SemesterResult, CourseGrade
from attendance.models import Course
from core.models import User
from django.db.models import Avg, Count
import decimal

@login_required
def student_results(request):
    results = SemesterResult.objects.filter(student=request.user).prefetch_related('grades')
    
    # Calculate some basics if results exist
    latest_result = results.last()
    cgpa = latest_result.cgpa if latest_result else 0
    total_credits = sum(r.credits_earned for r in results)
    
    context = {
        'results': results,
        'cgpa': cgpa,
        'total_credits': total_credits,
        'latest_semester': latest_result.semester if latest_result else 0
    }
    
    return render(request, 'results/student_results.html', context)

@login_required
def academic_hub(request):
    if request.user.role != 'FACULTY':
        messages.error(request, "Only faculty can access the Academic Hub.")
        return redirect('dashboard')
    
    my_courses = Course.objects.filter(faculty=request.user).annotate(
        student_count=Count('students'),
        avg_grade_points=Avg('course_grades__grade_points')
    )
    
    context = {
        'courses': my_courses,
    }
    return render(request, 'results/academic_hub.html', context)

@login_required
def manage_grades(request, course_id):
    if request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    students = course.students.all().order_by('username')
    
    # Get existing grades for this course
    existing_grades = CourseGrade.objects.filter(course=course).select_related('student')
    grade_map = {g.student_id: g for g in existing_grades}
    
    student_data = []
    for student in students:
        student_data.append({
            'student': student,
            'grade_obj': grade_map.get(student.id)
        })
        
    context = {
        'course': course,
        'student_data': student_data,
        'grade_options': ['O', 'A+', 'A', 'B+', 'B', 'C', 'P', 'F']
    }
    return render(request, 'results/manage_grades.html', context)

@login_required
def bulk_update_grades(request, course_id):
    if request.method != 'POST' or request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    
    grade_points_map = {
        'O': 10, 'A+': 9, 'A': 8, 'B+': 7, 'B': 6, 'C': 5, 'P': 4, 'F': 0
    }
    
    course_credits = 4 # Default credits if not specified, maybe add to Course model later
    
    for key, value in request.POST.items():
        if key.startswith('grade_'):
            student_id = key.split('_')[1]
            student = get_object_or_404(User, id=student_id)
            grade_letter = value
            
            if grade_letter not in grade_points_map:
                continue
                
            # Find or create SemesterResult for the student (assuming current sem 1 for mock)
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
            
            if total_creds > 0:
                sem_result.sgpa = decimal.Decimal(total_pts) / decimal.Decimal(total_creds)
                sem_result.total_credits = total_creds
                sem_result.credits_earned = sum(g.credits for g in all_grades if g.grade != 'F')
                # For mock, set CGPA same as SGPA if only 1 sem
                sem_result.cgpa = sem_result.sgpa
                sem_result.save()
                
    messages.success(request, f"Grades updated successfully for {course.code}")
    return redirect('academic_hub')
