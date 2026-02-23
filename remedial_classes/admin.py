from django.contrib import admin
from .models import RemedialSession, RemedialAttendance

@admin.register(RemedialSession)
class RemedialSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'faculty', 'date', 'start_time', 'unique_code', 'status', 'is_active')
    list_filter = ('status', 'is_active', 'date')
    search_fields = ('unique_code',)
    actions = ['approve_sessions', 'reject_sessions']
    
    def approve_sessions(self, request, queryset):
        queryset.filter(status='PENDING').update(status='APPROVED')
        self.message_user(request, "Selected make-up class proposals have been approved.")
        
    def reject_sessions(self, request, queryset):
        queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, "Selected make-up class proposals have been rejected.")

@admin.register(RemedialAttendance)
class RemedialAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'time_marked')
    list_filter = ('session__date',)
