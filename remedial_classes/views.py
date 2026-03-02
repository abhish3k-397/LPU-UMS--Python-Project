from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import RemedialSession
from attendance.models import Course
from core.models import Section
import json

@login_required
def faculty_remedial(request):
    if request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    sessions = RemedialSession.objects.filter(faculty=request.user).order_by('-date', '-slot_number')
    from resource_management.models import Classroom
    classrooms = Classroom.objects.filter(is_available=True, room_type__in=['CLASSROOM', 'LAB'])

    if request.method == 'POST':
        course_id = request.POST.get('course')
        section_id = request.POST.get('section')
        date = request.POST.get('date')
        slot_number = request.POST.get('slot_number')
        classroom_id = request.POST.get('classroom')
        
        course = get_object_or_404(Course, id=course_id, faculty=request.user)
        section = get_object_or_404(Section, id=section_id) if section_id else None
        classroom = get_object_or_404(Classroom, id=classroom_id) if classroom_id else None
        
        RemedialSession.objects.create(
            course=course,
            section=section,
            faculty=request.user,
            date=date,
            slot_number=slot_number,
            classroom=classroom,
            status='PENDING'
        )
        messages.success(request, f"Remedial class for {course.name} ({section.name if section else 'No Section'}) Slot {slot_number} proposed. Pending Admin Approval.")
        return redirect('faculty_remedial')
        
    return render(request, 'remedial_classes/faculty_dashboard.html', {
        'sessions': sessions,
        'courses': courses,
        'classrooms': classrooms,
        'data_map_json': data_map
    })

@login_required
def delete_remedial_session(request, session_id):
    if request.user.role == 'FACULTY':
        session = get_object_or_404(RemedialSession, id=session_id, faculty=request.user)
        # Check if attendance session has already been created for this remedial
        # We'll need more logic here later to check AttendanceSession, 
        # but for now let's just allow deletion.
        session.delete()
        messages.success(request, "Remedial session removed.")
    return redirect('faculty_remedial')

@login_required
def admin_remedial_approvals(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied. Admins only.")
        return redirect('dashboard')
        
    proposals = RemedialSession.objects.filter(status='PENDING').order_by('date', 'slot_number')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        session_id = request.POST.get('session_id')
        session = get_object_or_404(RemedialSession, id=session_id)
        
        if action == 'approve':
            session.status = 'APPROVED'
            session.save()
            messages.success(request, f"Approved Remedial Session for {session.course.code}.")
            
        elif action == 'reject':
            session.status = 'REJECTED'
            session.save()
            messages.warning(request, f"Rejected Remedial Session for {session.course.code}.")
            
        return redirect('admin_remedial_approvals')
        
    return render(request, 'remedial_classes/admin_approvals.html', {'proposals': proposals})
