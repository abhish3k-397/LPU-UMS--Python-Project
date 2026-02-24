from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Course, AttendanceSession, AttendanceRecord, AttendanceEditRequest, TimetableSlot
from django.utils import timezone
from core.models import User

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
def create_session(request, slot_id):
    slot = get_object_or_404(TimetableSlot, id=slot_id, course__faculty=request.user)
    
    # Check if session already exists for this slot today
    today = timezone.now().date()
    session = AttendanceSession.objects.filter(slot=slot, date=today).first()
    
    if not session:
        session = AttendanceSession.objects.create(
            course=slot.course,
            slot=slot,
            date=today
        )
        # Auto-create records for all students in this section
        section_students = User.objects.filter(role='STUDENT', section=slot.section)
        for student in section_students:
            AttendanceRecord.objects.get_or_create(session=session, student=student, defaults={'is_present': False})
            
        messages.success(request, f"Started attendance for {slot.course.code} (Section {slot.section.name})")
    
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
        session_id = request.POST.get('session_id')
        student_id = request.POST.get('student_id')
        requested_status = request.POST.get('requested_status') == 'true'
        reason = request.POST.get('reason')
        
        session = get_object_or_404(AttendanceSession, id=session_id, course__faculty=request.user)
        student = get_object_or_404(User, id=student_id, role='STUDENT')
        
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
    students = User.objects.filter(role='STUDENT').order_by('username')
    return render(request, 'attendance/request_edit.html', {
        'sessions': sessions,
        'students': students
    })

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

@login_required
def timetable_view(request):
    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    slots = range(1, 8)
    
    if request.user.role == 'FACULTY':
        timetable_slots = list(TimetableSlot.objects.filter(course__faculty=request.user))
    elif request.user.role == 'STUDENT':
        if request.user.section:
            timetable_slots = list(TimetableSlot.objects.filter(section=request.user.section))
        else:
            timetable_slots = []
            messages.warning(request, "You are not assigned to any section. Please contact admin.")
    else:
        return redirect('dashboard')
    
    # Organize data into rows for easy template iteration
    slot_times = {
        1: "09:00 - 10:00",
        2: "10:00 - 11:00",
        3: "11:00 - 12:00",
        4: "12:00 - 13:00",
        5: "13:00 - 14:00",
        6: "14:00 - 15:00",
        7: "15:00 - 16:00",
    }
    
    timetable_rows = []
    for slot_num in slots:
        row = {
            'slot_num': slot_num,
            'time_range': slot_times.get(slot_num, ""),
            'days': []
        }
        for day in days:
            match = next((s for s in timetable_slots if s.day_of_week == day and s.slot_number == slot_num), None)
            row['days'].append(match)
        timetable_rows.append(row)
        
    context = {
        'timetable_rows': timetable_rows,
        'day_labels': [{'code': d, 'name': dict(TimetableSlot.DAYS).get(d)} for d in days],
        'now': timezone.now()
    }
    return render(request, 'attendance/timetable.html', context)

@login_required
@user_passes_test(is_faculty)
def faculty_courses(request):
    courses = Course.objects.filter(faculty=request.user)
    course_list = []
    
    for course in courses:
        total_students = course.students.count()
        total_sessions = AttendanceSession.objects.filter(course=course).count()
        
        # Calculate average attendance for this course
        if total_sessions > 0:
            total_possible_attendance = total_students * total_sessions
            total_present_records = AttendanceRecord.objects.filter(
                session__course=course, 
                is_present=True
            ).count()
            avg_attendance = round((total_present_records / total_possible_attendance) * 100, 1)
        else:
            avg_attendance = 0.0
            
        recent_session = AttendanceSession.objects.filter(course=course).order_by('-date').first()
        
        course_list.append({
            'course': course,
            'total_students': total_students,
            'total_sessions': total_sessions,
            'avg_attendance': avg_attendance,
            'recent_session': recent_session
        })
        
    return render(request, 'attendance/faculty_courses.html', {'courses_data': course_list})

@login_required
@user_passes_test(is_faculty)
def course_sessions(request, course_id):
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    sessions = AttendanceSession.objects.filter(course=course).order_by('-date', '-slot__slot_number')
    
    total_students = course.students.count()
    session_data = []
    
    for session in sessions:
        present_count = AttendanceRecord.objects.filter(session=session, is_present=True).count()
        
        # Calculate times based on slot_number (Slot 1 = 9AM, Slot 2 = 10AM, etc.)
        start_hour = session.slot.slot_number + 8
        end_hour = start_hour + 1
        time_string = f"{start_hour:02d}:00 - {end_hour:02d}:00"
        
        session_data.append({
            'session': session,
            'present_count': present_count,
            'total_count': total_students,
            'percentage': round((present_count / total_students * 100), 1) if total_students > 0 else 0,
            'time_string': time_string
        })
        
    context = {
        'course': course,
        'sessions_data': session_data
    }
    return render(request, 'attendance/course_sessions.html', context)

@login_required
@user_passes_test(is_faculty)
def session_detail(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id, course__faculty=request.user)
    records = session.records.all().select_related('student')
    
    total_count = records.count()
    present_count = records.filter(is_present=True).count()
    percentage = (present_count / total_count * 100) if total_count > 0 else 0
    
    context = {
        'session': session,
        'records': records,
        'present_count': present_count,
        'total_count': total_count,
        'percentage': round(percentage, 1)
    }
    return render(request, 'attendance/session_detail.html', context)
