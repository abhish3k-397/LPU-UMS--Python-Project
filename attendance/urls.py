from django.urls import path
from . import views

urlpatterns = [
    path('', views.attendance_dashboard, name='attendance_dashboard'),
    path('slot/<int:slot_id>/start/', views.create_session, name='create_session'),
    path('session/<int:session_id>/mark/', views.mark_attendance, name='mark_attendance'),
    path('request-edit/', views.request_edit, name='request_edit'),
    path('approvals/', views.admin_attendance_approvals, name='admin_attendance_approvals'),
    path('timetable/', views.timetable_view, name='timetable'),
    path('faculty/courses/', views.faculty_courses, name='faculty_courses'),
    path('course/<int:course_id>/sessions/', views.course_sessions, name='course_sessions'),
    path('session/<int:session_id>/detail/', views.session_detail, name='session_detail'),
]
