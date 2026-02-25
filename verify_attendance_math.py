import os
import django
from django.utils import timezone
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from core.models import User, Section
from attendance.models import Course, AttendanceSession, AttendanceRecord, TimetableSlot
from remedial_classes.models import RemedialSession

def verify_math():
    print("Starting Attendance Math Verification...")
    
    # 1. Setup mock data
    student = User.objects.filter(role='STUDENT').first()
    faculty = User.objects.filter(role='FACULTY').first()
    course = Course.objects.first()
    section = student.section
    
    print(f"Testing for Student: {student.username} (Section: {section.name})")
    
    # Cleanup all existing records for this student to isolate math
    AttendanceRecord.objects.filter(student=student).delete()
    AttendanceSession.objects.filter(course=course).delete()
    
    # Create 2 regular sessions for THIS section
    slot = TimetableSlot.objects.filter(section=section, course=course).first()
    if not slot:
        slot = TimetableSlot.objects.create(day_of_week='MON', slot_number=1, course=course, section=section)
    
    s1 = AttendanceSession.objects.create(course=course, slot=slot, date=timezone.now().date() - timedelta(days=1))
    s2 = AttendanceSession.objects.create(course=course, slot=slot, date=timezone.now().date() - timedelta(days=2))
    
    # Create 1 regular session for DIFFERENT section
    other_section = Section.objects.exclude(id=section.id).first()
    other_slot = TimetableSlot.objects.filter(section=other_section, course=course).first()
    if not other_slot:
        other_slot = TimetableSlot.objects.create(day_of_week='MON', slot_number=2, course=course, section=other_section)
    
    s3 = AttendanceSession.objects.create(course=course, slot=other_slot, date=timezone.now().date() - timedelta(days=1))
    
    # Create 1 remedial session
    rs = RemedialSession.objects.create(course=course, faculty=faculty, date=timezone.now().date(), slot_number=5, status='APPROVED')
    s4 = AttendanceSession.objects.create(course=course, remedial_session=rs, date=timezone.now().date())
    
    # Mark student Present in 1 regular session (s1) and 1 remedial (s4)
    AttendanceRecord.objects.create(session=s1, student=student, is_present=True)
    AttendanceRecord.objects.create(session=s2, student=student, is_present=False)
    # Student shouldn't even have a record for s3 (different section), but let's be sure
    AttendanceRecord.objects.create(session=s4, student=student, is_present=True)
    
    print("--- Verification ---")
    
    # Check Overall Attendance (Academic Only)
    # Expected: 1/2 = 50.0% (s1 and s2 only. s3 is other section, s4 is remedial)
    total_records = AttendanceRecord.objects.filter(
        student=student, 
        session__remedial_session__isnull=True
    ).count()
    present_records = AttendanceRecord.objects.filter(
        student=student, 
        session__remedial_session__isnull=True,
        is_present=True
    ).count()
    calc_overall = round((present_records / total_records) * 100, 1) if total_records > 0 else 0
    
    print(f"Academic Records found: {total_records} (Expected: 2)")
    print(f"Academic Present: {present_records} (Expected: 1)")
    print(f"Calculated Overall: {calc_overall}% (Expected: 50.0%)")
    
    assert total_records == 2, f"Total records mismatch: {total_records}"
    assert present_records == 1, f"Present records mismatch: {present_records}"
    assert calc_overall == 50.0, f"Overall attendance mismatch: {calc_overall}"
    
    # Check Course Dashboard Logic
    total_sessions = AttendanceSession.objects.filter(
        course=course, 
        slot__section=student.section,
        remedial_session__isnull=True
    ).count()
    attended = AttendanceRecord.objects.filter(
        session__course=course, 
        session__slot__section=student.section,
        session__remedial_session__isnull=True,
        student=student, 
        is_present=True
    ).count()
    
    print(f"Course specific sessions: {total_sessions} (Expected: 2)")
    print(f"Course specific attended: {attended} (Expected: 1)")
    
    assert total_sessions == 2, f"Total course sessions mismatch: {total_sessions}"
    assert attended == 1, f"Course attended mismatch: {attended}"
    
    # Check Remedial count
    remedial_attended = AttendanceRecord.objects.filter(
        student=student, 
        session__remedial_session__isnull=False, 
        is_present=True
    ).count()
    print(f"Remedial Attended: {remedial_attended} (Expected: 1)")
    assert remedial_attended == 1, f"Remedial attended mismatch: {remedial_attended}"
    
    print("\nSUCCESS: Attendance math is correct and section-aware!")

if __name__ == '__main__':
    verify_math()
