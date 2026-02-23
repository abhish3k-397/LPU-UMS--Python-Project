from django.urls import path
from . import views

urlpatterns = [
    path('', views.resource_dashboard, name='resource_dashboard'),
]
