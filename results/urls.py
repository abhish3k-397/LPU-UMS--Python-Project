from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_results, name='student_results'),
    path('academic-hub/', views.academic_hub, name='academic_hub'),
    path('course/<int:course_id>/manage-grades/', views.manage_grades, name='manage_grades'),
    path('course/<int:course_id>/bulk-update-grades/', views.bulk_update_grades, name='bulk_update_grades'),
]
