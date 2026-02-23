from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import CampusBlock, Classroom
from attendance.models import Course
from django.db.models import Sum, Count
from core.models import User

@login_required
def resource_dashboard(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
        
    # Capacity Utilization Calculations
    blocks = CampusBlock.objects.annotate(
        total_classrooms=Count('classrooms'),
        total_capacity=Sum('classrooms__capacity')
    )
    
    total_uni_capacity = Classroom.objects.aggregate(Sum('capacity'))['capacity__sum'] or 0
    total_students = User.objects.filter(role='STUDENT', is_approved=True).count()
    
    utilization_percentage = 0
    if total_uni_capacity > 0:
        utilization_percentage = round((total_students / total_uni_capacity) * 100, 1)

    # Faculty Workload Distribution
    faculties = User.objects.filter(role='FACULTY', is_approved=True).annotate(
        course_count=Count('course')
    )
    
    # Calculate students per faculty
    workload_data = []
    for faculty in faculties:
        courses = Course.objects.filter(faculty=faculty)
        total_taught_students = sum(c.students.count() for c in courses)
        workload_data.append({
            'faculty': faculty,
            'course_count': faculty.course_count,
            'total_students': total_taught_students
        })
        
    # Sort by workload (heaviest first)
    workload_data.sort(key=lambda x: x['total_students'], reverse=True)

    return render(request, 'resource_management/dashboard.html', {
        'blocks': blocks,
        'total_uni_capacity': total_uni_capacity,
        'total_students': total_students,
        'utilization_percentage': utilization_percentage,
        'workload_data': workload_data
    })
