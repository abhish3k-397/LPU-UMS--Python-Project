from django.contrib import admin
from .models import Course, AttendanceSession, AttendanceRecord, AttendanceEditRequest

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'faculty')
    search_fields = ('code', 'name')
    filter_horizontal = ('students',)

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'date', 'created_at')
    list_filter = ('course', 'date')

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'is_present')
    list_filter = ('session', 'is_present')
