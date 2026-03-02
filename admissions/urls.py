from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.admissions_dashboard, name='admissions_dashboard'),
    path('approve/<int:app_id>/', views.approve_admission, name='approve_admission'),
    path('reject/<int:app_id>/', views.reject_admission, name='reject_admission'),
]
