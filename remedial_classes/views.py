from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RemedialSession, RemedialAttendance
from attendance.models import Course
import datetime

@login_required
def faculty_remedial(request):
    if request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    sessions = RemedialSession.objects.filter(faculty=request.user).order_by('-date', '-start_time')
    courses = Course.objects.filter(faculty=request.user)
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        date = request.POST.get('date')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        course = get_object_or_404(Course, id=course_id, faculty=request.user)
        
        RemedialSession.objects.create(
            course=course,
            faculty=request.user,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status='PENDING'
        )
        messages.success(request, f"Remedial class for {course.name} proposed. Pending Admin Approval.")
        return redirect('faculty_remedial')
        
    return render(request, 'remedial_classes/faculty_dashboard.html', {
        'sessions': sessions,
        'courses': courses
    })

@login_required
def student_remedial(request):
    if request.user.role != 'STUDENT':
        return redirect('dashboard')
        
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        
        try:
            session = RemedialSession.objects.get(unique_code=code, is_active=True, status='APPROVED')
            
            # Check if student is enrolled in the course
            if not session.course.students.filter(id=request.user.id).exists():
                messages.error(request, "You are not enrolled in the course for this remedial class.")
            else:
                # Mark attendance
                attendance, created = RemedialAttendance.objects.get_or_create(
                    session=session,
                    student=request.user
                )
                if created:
                    messages.success(request, f"Attendance marked successfully for {session.course.name} remedial class.")
                else:
                    messages.info(request, "You have already marked your attendance for this session.")
        except RemedialSession.DoesNotExist:
            messages.error(request, "Invalid or expired remedial code. Ensure the session is approved by Admin.")
            
        return redirect('student_remedial')
        
    my_attendances = RemedialAttendance.objects.filter(student=request.user).order_by('-time_marked')
    return render(request, 'remedial_classes/student_dashboard.html', {'attendances': my_attendances})

@login_required
def toggle_session_status(request, session_id):
    if request.user.role == 'FACULTY':
        session = get_object_or_404(RemedialSession, id=session_id, faculty=request.user)
        session.is_active = not session.is_active
        session.save()
        status = "activated" if session.is_active else "deactivated"
        messages.success(request, f"Remedial session {status}.")
    return redirect('faculty_remedial')

@login_required
def admin_remedial_approvals(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied. Admins only.")
        return redirect('dashboard')
        
    proposals = RemedialSession.objects.filter(status='PENDING').order_by('date', 'start_time')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        session_id = request.POST.get('session_id')
        session = get_object_or_404(RemedialSession, id=session_id)
        
        if action == 'approve':
            session.status = 'APPROVED'
            session.is_active = True # Automatically activate upon approval
            session.save()
            messages.success(request, f"Approved Remedial Session for {session.course.code}.")
            
        elif action == 'reject':
            session.status = 'REJECTED'
            session.save()
            messages.warning(request, f"Rejected Remedial Session for {session.course.code}.")
            
        return redirect('admin_remedial_approvals')
        
    return render(request, 'remedial_classes/admin_approvals.html', {'proposals': proposals})
