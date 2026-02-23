from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    path('slot/<int:slot_id>/start/', views.create_session, name='create_session'),
    path('session/<int:session_id>/mark/', views.mark_attendance, name='mark_attendance'),
    path('request-edit/', views.request_edit, name='request_edit'),
    path('approvals/', views.admin_attendance_approvals, name='admin_attendance_approvals'),
]
