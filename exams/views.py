from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from attendance.models import Course
from .models import Exam
from .forms import ExamForm

@login_required
def exam_list(request):
    if request.user.role == 'FACULTY':
        # Faculty sees exams for courses they teach
        course_ids = Course.objects.filter(faculty=request.user).values_list('id', flat=True)
        exams = Exam.objects.filter(course_id__in=course_ids).order_by('date')
    else:
        # Students see exams for courses they are enrolled in
        course_ids = Course.objects.filter(students=request.user).values_list('id', flat=True)
        exams = Exam.objects.filter(course_id__in=course_ids).order_by('date')
    
    return render(request, 'exams/exam_list.html', {'exams': exams})

@login_required
def create_exam(request):
    if request.user.role not in ['FACULTY', 'ADMIN']:
        messages.error(request, "You don't have permission to create exams.")
        return redirect('exam_list')
    
    if request.method == 'POST':
        form = ExamForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Exam scheduled successfully!")
            return redirect('exam_list')
    else:
        form = ExamForm(user=request.user)
        
    return render(request, 'exams/exam_form.html', {'form': form})
