from django.urls import path
from . import views

urlpatterns = [
    path('', views.student_results, name='student_results'),
]
