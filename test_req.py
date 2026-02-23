import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from django.test.client import Client
from core.models import User

user = User.objects.get(username="admin")
c = Client()
c.force_login(user)

print("--- Attendance ---")
try:
    resp1 = c.get('/attendance/')
    print("Attendance Route Status:", resp1.status_code)
except Exception as e:
    print("Attendance Exception:", e)

print("\n--- Food Ordering ---")
try:
    resp2 = c.get('/food/')
    print("Food Route Status:", resp2.status_code)
    if resp2.status_code == 302:
        resp2_redirect = c.get(resp2.url)
        print("Redirected to:", resp2.url)
        print("Redirect Response Status:", resp2_redirect.status_code)
except Exception as e:
    print("Food Exception:", e)

print("\n--- Remedial ---")
try:
    resp3 = c.get('/remedial/')
    print("Remedial Route Status:", resp3.status_code)
except Exception as e:
    print("Remedial Exception:", e)
