from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

class CustomUserManager(UserManager):
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        extra_fields.setdefault('is_approved', True)
        extra_fields.setdefault('is_active', True)
        return super().create_superuser(username, email, password, **extra_fields)

class Section(models.Model):
    name = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        FACULTY = "FACULTY", "Faculty"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.STUDENT)
    uid = models.CharField(max_length=8, unique=True, null=True, blank=True)
    section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    is_approved = models.BooleanField(default=False)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()}) - {'Approved' if self.is_approved else 'Pending'}"
