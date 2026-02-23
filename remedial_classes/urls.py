from django.urls import path
from . import views

urlpatterns = [
    path('faculty/', views.faculty_remedial, name='faculty_remedial'),
    path('student/', views.student_remedial, name='student_remedial'),
    path('session/<int:session_id>/toggle/', views.toggle_session_status, name='toggle_session_status'),
    path('approvals/', views.admin_remedial_approvals, name='admin_remedial_approvals'),
]
