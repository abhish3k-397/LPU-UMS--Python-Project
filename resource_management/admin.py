from django.contrib import admin
from .models import CampusBlock, Classroom

class ClassroomInline(admin.TabularInline):
    model = Classroom
    extra = 1

@admin.register(CampusBlock)
class CampusBlockAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    inlines = [ClassroomInline]

@admin.register(Classroom)
class ClassroomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'block', 'capacity')
    list_filter = ('block',)
    search_fields = ('room_number', 'block__name')
