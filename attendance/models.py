from django.db import models
from django.conf import settings
from django.utils import timezone
from core.models import Section

class Course(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'FACULTY'})
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='enrolled_courses', limit_choices_to={'role': 'STUDENT'})

    def __str__(self):
        return f"{self.code} - {self.name}"

class TimetableSlot(models.Model):
    DAYS = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
    ]
    
    day_of_week = models.CharField(max_length=3, choices=DAYS)
    slot_number = models.IntegerField(help_text="Slot 1-7 (e.g. 9AM to 4PM)")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='slots')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='timetable')

    @property
    def time_range(self):
        slot_times = {
            1: "09:00 - 10:00",
            2: "10:00 - 11:00",
            3: "11:00 - 12:00",
            4: "12:00 - 13:00",
            5: "13:00 - 14:00",
            6: "14:00 - 15:00",
            7: "15:00 - 16:00",
        }
        return slot_times.get(self.slot_number, f"Slot {self.slot_number}")

    def __str__(self):
        return f"{self.section.name} - {self.day_of_week} Slot {self.slot_number} ({self.course.code})"

class AttendanceSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    slot = models.ForeignKey(TimetableSlot, on_delete=models.CASCADE, null=True, blank=True)
    remedial_session = models.ForeignKey('remedial_classes.RemedialSession', on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # A session is unique by date and either its timetable slot or its remedial session
        unique_together = ('date', 'slot', 'remedial_session')

    def __str__(self):
        slot_info = f"Slot {self.slot.slot_number}" if self.slot else f"Remedial (Slot {self.remedial_session.slot_number})" if self.remedial_session else "N/A"
        return f"{self.course.code} - {self.date} ({slot_info})"

class AttendanceRecord(models.Model):
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    is_present = models.BooleanField(default=False)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.username} - {'Present' if self.is_present else 'Absent'} in {self.session}"

class AttendanceEditRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='edit_requests')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendance_edit_requests', limit_choices_to={'role': 'STUDENT'})
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'FACULTY'})
    
    requested_is_present = models.BooleanField(help_text="The new presence status requested")
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Edit Request by {self.faculty.username} for {self.student.username} on {self.session.date}"
