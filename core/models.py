from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        FACULTY = "FACULTY", "Faculty"
        ADMIN = "ADMIN", "Admin"

    role = models.CharField(max_length=50, choices=Role.choices, default=Role.STUDENT)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()}) - {'Approved' if self.is_approved else 'Pending'}"
