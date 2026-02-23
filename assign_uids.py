import os
import django
import random
import string

# Setup Django atmosphere
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lpu_ums_project.settings')
django.setup()

from core.models import User

def generate_uid(role):
    if role == 'STUDENT':
        return '123' + ''.join(random.choices(string.digits, k=5))
    elif role == 'FACULTY':
        return ''.join(random.choices(string.digits, k=4))
    return None

def main():
    users = User.objects.all()
    count = 0
    for user in users:
        # Check if student UID is compliant
        if user.role == 'STUDENT' and user.uid and user.uid.startswith('123'):
            continue
        # Check if faculty UID is compliant (already set)
        if user.role == 'FACULTY' and user.uid and len(user.uid) == 4:
            continue
        
        new_uid = generate_uid(user.role)
        if new_uid:
            # Simple collision check
            while User.objects.filter(uid=new_uid).exists():
                new_uid = generate_uid(user.role)
            
            user.uid = new_uid
            user.save()
            count += 1
            print(f"Assigned UID {new_uid} to {user.username} ({user.role})")
    
    print(f"Successfully assigned UIDs to {count} users.")

if __name__ == "__main__":
    main()
