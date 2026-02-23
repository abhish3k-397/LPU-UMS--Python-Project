from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import SemesterResult
from django.db.models import Avg

@login_required
def student_results(request):
    results = SemesterResult.objects.filter(student=request.user).prefetch_related('grades')
    
    # Calculate some basics if results exist
    latest_result = results.last()
    cgpa = latest_result.cgpa if latest_result else 0
    total_credits = sum(r.credits_earned for r in results)
    
    context = {
        'results': results,
        'cgpa': cgpa,
        'total_credits': total_credits,
        'latest_semester': latest_result.semester if latest_result else 0
    }
    
    return render(request, 'results/student_results.html', context)
