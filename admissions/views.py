from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import AdmissionApplication, AdmissionQuery

@login_required
def admissions_dashboard(request):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
        
    applications = AdmissionApplication.objects.all().order_by('-applied_on')
    queries = AdmissionQuery.objects.all().order_by('-created_at')
    
    # Statistics
    total_apps = applications.count()
    pending_apps = applications.filter(status='PENDING').count()
    approved_apps = applications.filter(status='APPROVED').count()
    rejected_apps = applications.filter(status='REJECTED').count()
    
    unresolved_queries = queries.filter(is_resolved=False).count()
    
    return render(request, 'admissions/dashboard.html', {
        'applications': applications,
        'queries': queries,
        'total_apps': total_apps,
        'pending_apps': pending_apps,
        'approved_apps': approved_apps,
        'rejected_apps': rejected_apps,
        'unresolved_queries': unresolved_queries,
    })

import random
import string
from django.contrib import messages
from core.models import User, Section
from attendance.models import Course, TimetableSlot
from resource_management.models import Classroom

def generate_uid(role):
    if role == 'STUDENT':
        return '123' + ''.join(random.choices(string.digits, k=5))
    elif role == 'FACULTY':
        return ''.join(random.choices(string.digits, k=4))
    return None

@login_required
def approve_admission(request, app_id):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
        
    try:
        app = AdmissionApplication.objects.get(id=app_id, status='PENDING')
    except AdmissionApplication.DoesNotExist:
        messages.error(request, 'Application not found or already processed.')
        return redirect('admissions_dashboard')
        
    # 1. Logic to find or create a section
    # Let's find a section that has less than 10 students
    sections = Section.objects.all().order_by('id')
    assigned_section = None
    
    for section in sections:
        if User.objects.filter(section=section, role='STUDENT').count() < 10:
            assigned_section = section
            break
            
    if not assigned_section:
        # Create a new section
        new_section_name = f"K26-{sections.count() + 1}"
        assigned_section = Section.objects.create(name=new_section_name)
    
    # 2. Logic to assign classroom to section if not already assigned via timetable
    # In this mock we assign it dynamically if the section has no slots, or we just rely on setup_project
    
    # 3. Create the User account
    first_name_part = app.student_name.split()[0].lower()
    base_username = first_name_part
    username = base_username
    counter = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
        
    student = User.objects.create_user(
        username=username,
        email=app.email,
        password='123',
        role='STUDENT',
        section=assigned_section,
        is_approved=True,
        is_active=True
    )
    student.uid = generate_uid('STUDENT')
    while User.objects.filter(uid=student.uid).exclude(id=student.id).exists():
        student.uid = generate_uid('STUDENT')
    student.save()
    
    # Auto-enroll in all courses for the mock
    courses = Course.objects.all()
    for c in courses:
        c.students.add(student)
        
    # Mark app as approved
    app.status = 'APPROVED'
    app.save()
    
    messages.success(request, f'Admission approved for {app.student_name}. Account {student.username} created and assigned to {assigned_section.name}.')
    return redirect('admissions_dashboard')

@login_required
def reject_admission(request, app_id):
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    try:
        app = AdmissionApplication.objects.get(id=app_id, status='PENDING')
        app.status = 'REJECTED'
        app.save()
        messages.success(request, f'Application for {app.student_name} rejected.')
    except AdmissionApplication.DoesNotExist:
        messages.error(request, 'Application not found or already processed.')
    return redirect('admissions_dashboard')
