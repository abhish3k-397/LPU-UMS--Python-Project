from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register_view, name='register'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('approve-user/<int:user_id>/', views.approve_user, name='approve_user'),
    path('delete-user/<int:user_id>/', views.delete_user, name='delete_user'),
    path('student-courses/', views.student_courses, name='student_courses'),
    path('student-faculties/', views.student_faculties, name='student_faculties'),
    path('download-pdf/<str:file_type>/', views.download_empty_pdf, name='download_empty_pdf'),
]
