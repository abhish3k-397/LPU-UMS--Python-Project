from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Course, AttendanceSession, AttendanceRecord, AttendanceEditRequest
from django.utils import timezone

def is_faculty(user):
    return user.is_authenticated and user.role == 'FACULTY'

def is_student(user):
    return user.is_authenticated and user.role == 'STUDENT'

@login_required
def attendance_dashboard(request):
    if request.user.role == 'FACULTY':
        courses = Course.objects.filter(faculty=request.user)
        return render(request, 'attendance/faculty_dashboard.html', {'courses': courses})
    elif request.user.role == 'STUDENT':
        courses = Course.objects.filter(students=request.user)
        course_data = []
        for course in courses:
            total_sessions = AttendanceSession.objects.filter(course=course).count()
            attended = AttendanceRecord.objects.filter(session__course=course, student=request.user, is_present=True).count()
            percentage = int((attended / total_sessions) * 100) if total_sessions > 0 else 0
            
            course_data.append({
                'course': course,
                'total_sessions': total_sessions,
                'attended': attended,
                'percentage': percentage
            })
            
        return render(request, 'attendance/student_dashboard.html', {'course_data': course_data})
    else:
        return render(request, 'attendance/admin_dashboard.html')

@login_required
@user_passes_test(is_faculty)
def create_session(request, course_id):
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    
    # Check if session already exists for today to avoid duplicates and handle 500 crashes
    today = timezone.now().date()
    session = AttendanceSession.objects.filter(course=course, date=today).first()
    
    if not session:
        session = AttendanceSession.objects.create(course=course, date=today)
        # Auto-create records for all enrolled students defaulting to Absent
        for student in course.students.all():
            AttendanceRecord.objects.create(session=session, student=student, is_present=False)
        messages.success(request, f"Started new attendance session for {course.name}")
    
    return redirect('mark_attendance', session_id=session.id)

@login_required
@user_passes_test(is_faculty)
def mark_attendance(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id, course__faculty=request.user)
    records = session.records.all()
    
    if request.method == 'POST':
        # One-click bulk marking
        present_student_ids = request.POST.getlist('present_students')
        
        # Reset all to absent first
        records.update(is_present=False)
        
        # Mark selected as present
        if present_student_ids:
            records.filter(student_id__in=present_student_ids).update(is_present=True)
            
        messages.success(request, "Attendance saved successfully.")
        return redirect('dashboard')
        
    return render(request, 'attendance/mark_attendance.html', {'session': session, 'records': records})

@login_required
@user_passes_test(is_faculty)
def request_edit(request):
    if request.method == 'POST':
        from core.models import User
        from .models import AttendanceEditRequest
        
        session_id = request.POST.get('session_id')
        student_id = request.POST.get('student_id')
        requested_status = request.POST.get('requested_status') == 'true'
        reason = request.POST.get('reason')
        
        session = get_object_or_404(AttendanceSession, id=session_id, course__faculty=request.user)
        student = get_object_or_404(User, username=student_id, role='STUDENT')
        
        # Prevent duplicates
        if AttendanceEditRequest.objects.filter(session=session, student=student, status='PENDING').exists():
            messages.error(request, "A pending request for this student's attendance on this date already exists.")
            return redirect('dashboard')
            
        AttendanceEditRequest.objects.create(
            session=session,
            student=student,
            faculty=request.user,
            requested_is_present=requested_status,
            reason=reason,
            status='PENDING'
        )
        
        messages.success(request, f"Edit request for {student.username}'s attendance submitted for Admin approval.")
        return redirect('dashboard')
    
    # Render the request form
    sessions = AttendanceSession.objects.filter(course__faculty=request.user).order_by('-date')
    return render(request, 'attendance/request_edit.html', {'sessions': sessions})

@login_required
def admin_attendance_approvals(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied. Admins only.")
        return redirect('dashboard')
        
    requests = AttendanceEditRequest.objects.filter(status='PENDING').order_by('created_at')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        request_id = request.POST.get('request_id')
        edit_req = get_object_or_404(AttendanceEditRequest, id=request_id)
        
        if action == 'approve':
            edit_req.status = 'APPROVED'
            edit_req.resolved_at = timezone.now()
            edit_req.save()
            
            # Apply the change to the actual attendance record
            record = AttendanceRecord.objects.get(session=edit_req.session, student=edit_req.student)
            record.is_present = edit_req.requested_is_present
            record.save()
            messages.success(request, f"Approved request. {edit_req.student.username}'s attendance updated.")
            
        elif action == 'reject':
            edit_req.status = 'REJECTED'
            edit_req.resolved_at = timezone.now()
            edit_req.save()
            messages.warning(request, f"Rejected request for {edit_req.student.username}.")
            
        return redirect('admin_attendance_approvals')
        
    return render(request, 'attendance/admin_approvals.html', {'requests': requests})
