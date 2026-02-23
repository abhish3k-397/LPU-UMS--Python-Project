from django.db import models
from django.conf import settings
from attendance.models import Course

class Exam(models.Model):
    EXAM_TYPES = [
        ('CA', 'Continuous Assessment (CA)'),
        ('MID', 'Mid Term Examination'),
        ('END', 'End Term Examination'),
    ]

    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    date = models.DateTimeField()
    syllabus = models.FileField(upload_to='exams/syllabi/', null=True, blank=True)
    resources = models.FileField(upload_to='exams/resources/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.course.code} - {self.get_exam_type_display()}"
