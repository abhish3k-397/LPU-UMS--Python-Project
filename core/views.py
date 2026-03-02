from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from django import forms

from admissions.models import AdmissionApplication

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = AdmissionApplication
        fields = ['student_name', 'email', 'phone', 'course_applied']

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application submitted successfully! Our admissions team will review it shortly.')
            return redirect('login')
    else:
        form = RegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard_view(request):
    context = {}
    if request.user.role == 'ADMIN':
        from attendance.models import AttendanceEditRequest
        from remedial_classes.models import RemedialSession
        context['pending_edits'] = AttendanceEditRequest.objects.filter(status='PENDING').count()
        context['pending_remedials'] = RemedialSession.objects.filter(status='PENDING').count()
    elif request.user.role == 'FACULTY':
        from attendance.models import Course, AttendanceSession, AttendanceEditRequest, TimetableSlot
        from django.utils import timezone
        import datetime
        
        now = timezone.localtime()
        today = now.date()
        
        # Determine current slot
        # Slot 1: 9-10, Slot 2: 10-11, ..., Slot 7: 15-16
        current_hour = now.hour
        current_slot_num = None
        if 9 <= current_hour < 16:
            current_slot_num = current_hour - 8
        
        # Determine current day (0=Mon, 4=Fri)
        days_map = {0: 'MON', 1: 'TUE', 2: 'WED', 3: 'THU', 4: 'FRI'}
        current_day_code = days_map.get(now.weekday())
        
        from remedial_classes.models import RemedialSession
        
        active_slots = []
        if current_day_code:
            # Find all timetable slots for this faculty for the entire current day
            faculty_slots = TimetableSlot.objects.filter(
                course__faculty=request.user,
                day_of_week=current_day_code
            ).order_by('slot_number')
            
            for slot in faculty_slots:
                # Check if session already exists for this slot today
                session_exists = AttendanceSession.objects.filter(
                    slot=slot,
                    date=today
                ).exists()
                
                slot.is_punched = session_exists
                # Tag the slot if it's currently active (matching current hour)
                slot.is_current = (slot.slot_number == current_slot_num)
                slot.is_remedial = False
                active_slots.append(slot)
            
            # Find approved remedial sessions for today
            remedial_sessions = RemedialSession.objects.filter(
                faculty=request.user,
                date=today,
                status='APPROVED'
            )
            
            for rs in remedial_sessions:
                # Check if attendance session exists for this remedial
                # Since remedial sessions are one-off, we can link them to course + date + slot
                session_exists = AttendanceSession.objects.filter(
                    remedial_session=rs,
                    date=today
                ).exists()
                
                # Mocking a slot-like object for the UI
                rs.slot_number = rs.slot_number # already exists
                rs.is_punched = session_exists
                rs.is_current = (rs.slot_number == current_slot_num)
                rs.is_remedial = True
                active_slots.append(rs)
            
            # Re-sort everything by slot number
            active_slots.sort(key=lambda x: x.slot_number)
        
        context['active_slots'] = active_slots
        
        assigned_courses = Course.objects.filter(faculty=request.user)
        context['total_students'] = assigned_courses.values('students').distinct().count()
        context['total_courses_count'] = assigned_courses.count()
        
        context['active_sessions_today'] = AttendanceSession.objects.filter(
            course__faculty=request.user, 
            date=today
        ).count()
        
        context['pending_edits_count'] = AttendanceEditRequest.objects.filter(
            session__course__faculty=request.user,
            status='PENDING'
        ).count()
    elif request.user.role == 'STUDENT':
        from attendance.models import Course, AttendanceRecord
        from results.models import SemesterResult
        
        courses = Course.objects.filter(students=request.user)
        context['enrolled_courses_count'] = courses.count()
        
        # Calculate overall attendance percentage (Academic only, excluding remedial)
        from attendance.models import AttendanceRecord
        total_records = AttendanceRecord.objects.filter(
            student=request.user, 
            session__remedial_session__isnull=True
        ).count()
        if total_records > 0:
            present_records = AttendanceRecord.objects.filter(
                student=request.user, 
                session__remedial_session__isnull=True,
                is_present=True
            ).count()
            context['overall_attendance'] = round((present_records / total_records) * 100, 1)
        else:
            context['overall_attendance'] = "0.0"
            
        # Get latest academic metrics from results
        latest_result = SemesterResult.objects.filter(student=request.user).order_by('-semester').first()
        if latest_result:
            context['latest_sgpa'] = latest_result.sgpa
            context['credits_progress'] = f"{latest_result.credits_earned}/{latest_result.total_credits}"
        else:
            context['latest_sgpa'] = "0.0"
            context['credits_progress'] = "0/0"
            
        from attendance.models import AttendanceRecord
        context['remedial_attended'] = AttendanceRecord.objects.filter(
            student=request.user, 
            session__remedial_session__isnull=False, 
            is_present=True
        ).count()
    
    return render(request, 'core/dashboard.html', context)

@login_required
def admin_panel(request):
    from django.shortcuts import get_object_or_404
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied. Admin only.")
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_panel.html', {'users': users})

@login_required
def approve_user(request, user_id):
    from django.shortcuts import get_object_or_404
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    user_to_approve = get_object_or_404(User, id=user_id)
    user_to_approve.is_approved = True
    user_to_approve.is_active = True
    user_to_approve.save()
    messages.success(request, f"User {user_to_approve.username} approved successfully.")
    return redirect('admin_panel')

@login_required
def delete_user(request, user_id):
    from django.shortcuts import get_object_or_404
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
        
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete yourself.")
    else:
        user_to_delete.delete()
        messages.success(request, f"User {user_to_delete.username} deleted.")
    return redirect('admin_panel')
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.role == 'STUDENT')
def student_courses(request):
    from attendance.models import Course
    courses = Course.objects.filter(students=request.user)
    return render(request, 'core/student_courses.html', {'courses': courses})

@login_required
def download_empty_pdf(request, file_type):
    from django.http import HttpResponse
    # A minimal valid PDF file (0 bytes content, standard header/footer)
    minimal_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    response = HttpResponse(minimal_pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dummy_{file_type}.pdf"'
    return response

@login_required
@user_passes_test(lambda u: u.role == 'STUDENT')
def student_faculties(request):
    from attendance.models import Course
    # Get all courses the student is enrolled in
    courses = Course.objects.filter(students=request.user).select_related('faculty')
    
    # Extract unique faculties and their associated courses for this student
    faculty_data = {}
    for course in courses:
        faculty = course.faculty
        if faculty not in faculty_data:
            faculty_data[faculty] = []
        faculty_data[faculty].append(course)
        
    context = {
        'faculty_data': faculty_data
    }
    return render(request, 'core/student_faculties.html', context)
