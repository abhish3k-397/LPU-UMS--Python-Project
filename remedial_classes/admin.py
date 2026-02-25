from django.contrib import admin
from .models import RemedialSession

@admin.register(RemedialSession)
class RemedialSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'section', 'faculty', 'date', 'slot_number', 'status')
    list_filter = ('status', 'date', 'slot_number')
    search_fields = ('course__code', 'course__name', 'faculty__username')
    actions = ['approve_sessions', 'reject_sessions']
    
    def approve_sessions(self, request, queryset):
        queryset.filter(status='PENDING').update(status='APPROVED')
        self.message_user(request, "Selected remedial class proposals have been approved.")
        
    def reject_sessions(self, request, queryset):
        queryset.filter(status='PENDING').update(status='REJECTED')
        self.message_user(request, "Selected remedial class proposals have been rejected.")
