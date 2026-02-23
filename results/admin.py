from django.contrib import admin
from .models import SemesterResult, CourseGrade

class CourseGradeInline(admin.TabularInline):
    model = CourseGrade
    extra = 1

@admin.register(SemesterResult)
class SemesterResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'semester', 'sgpa', 'cgpa', 'credits_earned')
    list_filter = ('semester', 'student')
    inlines = [CourseGradeInline]

@admin.register(CourseGrade)
class CourseGradeAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name', 'grade', 'semester_result')
    list_filter = ('grade', 'course_code')
