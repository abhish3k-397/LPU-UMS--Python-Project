import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lpu_ums_project.settings")
django.setup()

from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from results.views import calculate_final_grades
from core.models import User, Section
from attendance.models import Course
from results.models import CourseGrade

faculty = User.objects.get(username='Gauth')
course = Course.objects.get(code='CSE401')
section = Section.objects.get(name='K23RT')

factory = RequestFactory()
request = factory.post(f'/dummy/{course.id}/{section.id}/')
request.user = faculty
# Patch messages
setattr(request, 'session', 'session')
messages = FallbackStorage(request)
setattr(request, '_messages', messages)

# Execute the view logic
response = calculate_final_grades(request, course.id, section.id)
print("Response status code:", response.status_code)

# Check grades
grades = CourseGrade.objects.filter(course=course, student__section=section).order_by('-net_marks', 'student__username')
for g in grades:
    print(f"{g.student.username}: {g.net_marks} - {g.grade}")
