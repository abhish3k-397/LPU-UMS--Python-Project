from django.db import models
from django.conf import settings
from attendance.models import Course

class SemesterResult(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='semester_results')
    semester = models.IntegerField()  # 1, 2, 3 etc.
    sgpa = models.DecimalField(max_digits=4, decimal_places=2)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    credits_earned = models.IntegerField()
    total_credits = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['semester']

    def __str__(self):
        return f"{self.student.username} - Sem {self.semester}"

class CourseGrade(models.Model):
    semester_result = models.ForeignKey(SemesterResult, on_delete=models.CASCADE, related_name='grades')
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20)
    grade = models.CharField(max_length=2)  # O, A+, A, B+, B, C, P, F
    grade_points = models.IntegerField()
    credits = models.IntegerField()

    def __str__(self):
        return f"{self.course_code}: {self.grade}"
