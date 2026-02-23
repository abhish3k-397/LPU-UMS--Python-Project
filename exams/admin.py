from django.contrib import admin
from .models import Exam

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'exam_type', 'date', 'created_at')
    list_filter = ('exam_type', 'date')
    search_fields = ('course__name', 'course__code')
