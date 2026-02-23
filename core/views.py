from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User
from django import forms

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            self.add_error('confirm_password', "Passwords do not match")
        
        return cleaned_data

def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            # Ensure users require admin approval
            user.is_approved = False
            user.is_active = False # Django won't let them login if is_active is False
            user.save()
            messages.success(request, 'Registration successful. Please wait for an Admin to approve your account.')
            return redirect('login')
    else:
        form = RegistrationForm()
        
    return render(request, 'core/register.html', {'form': form})

@login_required
def dashboard_view(request):
    context = {}
    if request.user.role == 'ADMIN':
        from attendance.models import AttendanceEditRequest
        from remedial_classes.models import RemedialSession
        context['pending_edits'] = AttendanceEditRequest.objects.filter(status='PENDING').count()
        context['pending_remedials'] = RemedialSession.objects.filter(status='PENDING').count()
    elif request.user.role == 'FACULTY':
        from attendance.models import Course
        context['courses'] = Course.objects.filter(faculty=request.user)
    elif request.user.role == 'STUDENT':
        from attendance.models import Course, AttendanceRecord
        from remedial_classes.models import RemedialAttendance
        
        courses = Course.objects.filter(students=request.user)
        context['enrolled_courses'] = courses
        context['total_sessions'] = AttendanceRecord.objects.filter(student=request.user, is_present=True).count()
        context['remedial_attended'] = RemedialAttendance.objects.filter(student=request.user).count()
    
    return render(request, 'core/dashboard.html', context)

@login_required
def admin_panel(request):
    from django.shortcuts import get_object_or_404
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied. Admin only.")
        return redirect('dashboard')
    
    users = User.objects.all().order_by('-date_joined')
    return render(request, 'core/admin_panel.html', {'users': users})

@login_required
def approve_user(request, user_id):
    from django.shortcuts import get_object_or_404
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
    
    user_to_approve = get_object_or_404(User, id=user_id)
    user_to_approve.is_approved = True
    user_to_approve.is_active = True
    user_to_approve.save()
    messages.success(request, f"User {user_to_approve.username} approved successfully.")
    return redirect('admin_panel')

@login_required
def delete_user(request, user_id):
    from django.shortcuts import get_object_or_404
    if request.user.role != 'ADMIN':
        return redirect('dashboard')
        
    user_to_delete = get_object_or_404(User, id=user_id)
    if user_to_delete == request.user:
        messages.error(request, "You cannot delete yourself.")
    else:
        user_to_delete.delete()
        messages.success(request, f"User {user_to_delete.username} deleted.")
    return redirect('admin_panel')
from django.contrib.auth.decorators import user_passes_test

@login_required
@user_passes_test(lambda u: u.role == 'STUDENT')
def student_courses(request):
    from attendance.models import Course
    courses = Course.objects.filter(students=request.user)
    return render(request, 'core/student_courses.html', {'courses': courses})

@login_required
def download_empty_pdf(request, file_type):
    from django.http import HttpResponse
    # A minimal valid PDF file (0 bytes content, standard header/footer)
    minimal_pdf = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF"
    response = HttpResponse(minimal_pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="dummy_{file_type}.pdf"'
    return response

@login_required
@user_passes_test(lambda u: u.role == 'STUDENT')
def student_faculties(request):
    from attendance.models import Course
    # Get all courses the student is enrolled in
    courses = Course.objects.filter(students=request.user).select_related('faculty')
    
    # Extract unique faculties and their associated courses for this student
    faculty_data = {}
    for course in courses:
        faculty = course.faculty
        if faculty not in faculty_data:
            faculty_data[faculty] = []
        faculty_data[faculty].append(course)
        
    context = {
        'faculty_data': faculty_data
    }
    return render(request, 'core/student_faculties.html', context)
