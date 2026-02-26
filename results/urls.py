from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_results, name='student_results'),
    path('academic-hub/', views.academic_hub, name='academic_hub'),
    path('course/<int:course_id>/manage-grades/', views.manage_grades, name='manage_grades'),
    path('course/<int:course_id>/section/<int:section_id>/exams/', views.manage_section_exams, name='manage_section_exams'),
    path('course/<int:course_id>/section/<int:section_id>/exam/<int:exam_id>/', views.manage_exam_marks, name='manage_exam_marks'),
    path('course/<int:course_id>/section/<int:section_id>/calculate-grades/', views.calculate_final_grades, name='calculate_final_grades'),
]
