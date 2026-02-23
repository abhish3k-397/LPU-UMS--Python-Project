from django.db import models
from django.conf import settings
from attendance.models import Course
import random
import string

def generate_unique_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

class RemedialSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'FACULTY'})
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    STATUS_CHOICES = [
        ('PENDING', 'Pending Admin Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    unique_code = models.CharField(max_length=10, default=generate_unique_code, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} Remedial - {self.date}"

class RemedialAttendance(models.Model):
    session = models.ForeignKey(RemedialSession, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'STUDENT'})
    time_marked = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('session', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.session}"
