import os
import django
import random
import string

# Setup Django atmosphere
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from core.models import User, Section
from attendance.models import Course, TimetableSlot

def generate_uid(role):
    if role == 'STUDENT':
        return '123' + ''.join(random.choices(string.digits, k=5))
    elif role == 'FACULTY':
        return ''.join(random.choices(string.digits, k=4))
    return None

def main():
    # 1. Create Sections
    section_names = ['K23RT', 'K23PT', 'K23HG']
    sections = []
    for name in section_names:
        section, created = Section.objects.get_or_create(name=name)
        sections.append(section)
        if created:
            print(f"Created Section: {name}")

    # 2. Create 30 Students (10 per section)
    student_names = [
        "Aarav", "Ishani", "Vihaan", "Advika", "Reyansh", "Myra", "Siddharth", "Ananya", "Kabir", "Zara",
        "Rohan", "Sanya", "Arjun", "Kritika", "Dhruv", "Riya", "Aryan", "Pooja", "Kartik", "Sneha",
        "Aditya", "Tanvi", "Pranav", "Ishita", "Rahul", "Mehak", "Dev", "Kyra", "Yash", "Avni"
    ]
    
    all_courses = list(Course.objects.all())
    
    for i, name in enumerate(student_names):
        section = sections[i // 10]
        username = f"{name}_{section.name}"
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'role': 'STUDENT',
                'section': section,
                'is_approved': True
            }
        )
        if created:
            user.set_password('password123')
            user.uid = generate_uid('STUDENT')
            # Collision check
            while User.objects.filter(uid=user.uid).exclude(id=user.id).exists():
                user.uid = generate_uid('STUDENT')
            user.save()
            # Enroll in all courses
            for course in all_courses:
                course.students.add(user)
            print(f"Created Student: {username} (ID: {user.uid}) in {section.name}")

    # 3. Create Fixed Timetable
    # 5 courses, 3 sections, 4 slots/course/section = 60 slots total
    # 5 days, 7 slots/day = 35 possible slot positions per section
    # Total needed slots: 20 per section.
    
    TimetableSlot.objects.all().delete()
    print("Cleared existing TimetableSlots.")

    days = ['MON', 'TUE', 'WED', 'THU', 'FRI']
    
    # Simple algorithm to avoid faculty clash
    # Slot map: (day, slot_number) -> set of courses being taught
    activity_map = {}

    for section in sections:
        course_slots_count = {course.id: 0 for course in all_courses}
        
        # We need 20 slots for this section
        for day in days:
            slots_for_today = 0
            for slot_num in range(1, 8):
                if slots_for_today >= 4: # Max 4 classes per day per section for balance
                    continue
                
                # Pick a course that hasn't reached 4 slots yet and faculty is free
                random.shuffle(all_courses)
                for course in all_courses:
                    if course_slots_count[course.id] < 4:
                        # Check if faculty is teaching elsewhere at this time
                        key = (day, slot_num)
                        if key not in activity_map:
                            activity_map[key] = set()
                        
                        if course.id not in activity_map[key]:
                            # Assign!
                            TimetableSlot.objects.create(
                                day_of_week=day,
                                slot_number=slot_num,
                                course=course,
                                section=section
                            )
                            activity_map[key].add(course.id)
                            course_slots_count[course.id] += 1
                            slots_for_today += 1
                            break
        
        print(f"Generated 20-slot timetable for {section.name}")

    print("Timetable population complete.")

if __name__ == "__main__":
    main()
