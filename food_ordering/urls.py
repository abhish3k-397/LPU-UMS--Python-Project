from django.urls import path
from . import views

urlpatterns = [
    path('', views.food_dashboard, name='food_dashboard'),
    path('menu/', views.student_menu, name='student_menu'),
    path('stall-admin/', views.stall_admin_dashboard, name='stall_admin_dashboard'),
]
