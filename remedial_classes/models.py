from django.db import models
from django.conf import settings
from attendance.models import Course
from core.models import Section

class RemedialSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, null=True, blank=True)
    faculty = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'FACULTY'})
    date = models.DateField()
    slot_number = models.IntegerField(help_text="Slot 1-7")
    classroom = models.ForeignKey('resource_management.Classroom', on_delete=models.SET_NULL, null=True, blank=True, related_name='remedial_sessions')
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending Admin Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

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
        return f"{self.course.code} Remedial ({self.time_range}) - {self.date}"
