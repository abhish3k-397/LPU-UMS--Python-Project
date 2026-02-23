from django.contrib import admin
from .models import FoodItem, TimeSlot, OrderGroup, OrderItem

@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available')
    list_filter = ('is_available',)
    search_fields = ('name',)

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time')

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(OrderGroup)
class OrderGroupAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'time_slot', 'status', 'created_at', 'total_price')
    list_filter = ('status', 'time_slot', 'created_at')
    search_fields = ('student__username',)
    inlines = [OrderItemInline]

