from django.db import models
from django.conf import settings
from attendance.models import Course
from core.models import Section
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_grades', null=True, blank=True)
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='individual_grades', null=True, blank=True)
    course_name = models.CharField(max_length=100) # Keep for redundancy/history
    course_code = models.CharField(max_length=20) # Keep for redundancy/history
    grade = models.CharField(max_length=2)  # O, A+, A, B+, B, C, D, E
    grade_points = models.IntegerField()
    credits = models.IntegerField()
    net_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Detailed Extracted Marks (out of their respective max marks, e.g. 30, 30, 30, 30, 60)
    ca1_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ca2_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    ca3_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    mid_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    end_marks = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Weighted Components (e.g. CA weight out of 25, MID 20, END 50, ATT 5)
    ca_weighted = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    mid_weighted = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    end_weighted = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    att_weighted = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)


    def __str__(self):
        return f"{self.course_code}: {self.grade}"

class Exam(models.Model):
    EXAM_TYPES = [
        ('CA1', 'CA 1'),
        ('CA2', 'CA 2'),
        ('CA3', 'CA 3'),
        ('MID', 'Mid Term'),
        ('END', 'End Term'),
    ]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='results_exams')
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='results_exams')
    exam_type = models.CharField(max_length=3, choices=EXAM_TYPES)
    max_marks = models.IntegerField()
    
    class Meta:
        unique_together = ('course', 'section', 'exam_type')
        
    def __str__(self):
        return f"{self.course.code} - {self.section.name} - {self.get_exam_type_display()}"

class StudentExamMark(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='marks')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_marks')
    marks_obtained = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        unique_together = ('exam', 'student')

    def __str__(self):
        return f"{self.student.username} - {self.exam.get_exam_type_display()}: {self.marks_obtained}/{self.exam.max_marks}"
