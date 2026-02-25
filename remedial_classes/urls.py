from django.urls import path
from . import views

urlpatterns = [
    path('faculty/', views.faculty_remedial, name='faculty_remedial'),
    path('delete/<int:session_id>/', views.delete_remedial_session, name='delete_remedial_session'),
    path('approvals/', views.admin_remedial_approvals, name='admin_remedial_approvals'),
]
