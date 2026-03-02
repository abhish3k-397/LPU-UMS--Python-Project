from django import forms
from .models import Exam
from attendance.models import Course

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['course', 'exam_type', 'date', 'classroom', 'syllabus', 'resources']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-input w-full rounded-xl border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white'}),
            'course': forms.Select(attrs={'class': 'form-select w-full rounded-xl border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white'}),
            'exam_type': forms.Select(attrs={'class': 'form-select w-full rounded-xl border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white'}),
            'syllabus': forms.FileInput(attrs={'class': 'form-input w-full rounded-xl border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white', 'accept': '.pdf,.doc,.docx'}),
            'resources': forms.FileInput(attrs={'class': 'form-input w-full rounded-xl border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white', 'accept': '.pdf,.zip,.rar'}),
            'classroom': forms.Select(attrs={'class': 'form-select w-full rounded-xl border-slate-200 dark:border-slate-700 dark:bg-slate-800 dark:text-white'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.role == 'FACULTY':
                # Faculty can only create CAs for their own courses
                self.fields['course'].queryset = Course.objects.filter(faculty=user)
                self.fields['exam_type'].choices = [('CA', 'Continuous Assessment (CA)')]
            elif user.role == 'ADMIN':
                # Admin can create anything for any course
                self.fields['course'].queryset = Course.objects.all()
