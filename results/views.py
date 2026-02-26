from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import SemesterResult, CourseGrade
from attendance.models import Course
from core.models import User, Section
from django.db.models import Avg, Count
import decimal

@login_required
def student_results(request):
    all_results = SemesterResult.objects.filter(student=request.user).prefetch_related('grades').order_by('semester')
    
    # Only keep results that actually have grades published in them
    results = [r for r in all_results if r.grades.exists()]
    
    # Calculate basics and recalculate SGPA/CGPA properly
    cum_pts = 0
    cum_creds = 0
    total_credits = 0
    
    for result in results:
        sem_pts = 0
        sem_creds = 0
        earned_creds = 0
        
        for grade in result.grades.all():
            sem_pts += grade.grade_points * grade.credits
            sem_creds += grade.credits
            if grade.grade != 'E':
                earned_creds += grade.credits
                
        if sem_creds > 0:
            result.sgpa = round(decimal.Decimal(sem_pts) / decimal.Decimal(sem_creds), 2)
            result.total_credits = sem_creds
            result.credits_earned = earned_creds
            
        cum_pts += sem_pts
        cum_creds += sem_creds
        
        if cum_creds > 0:
            result.cgpa = round(decimal.Decimal(cum_pts) / decimal.Decimal(cum_creds), 2)
        else:
            result.cgpa = result.sgpa
            
        result.save()
        total_credits += earned_creds
        
    latest_result = results[-1] if results else None
    cgpa = latest_result.cgpa if latest_result else decimal.Decimal('0.00')
    
    # Find ongoing/awaited courses
    active_courses = Course.objects.filter(students=request.user)
    graded_course_ids = CourseGrade.objects.filter(student=request.user).values_list('course_id', flat=True)
    
    awaited_courses = []
    for course in active_courses:
        if course.id not in graded_course_ids:
            awaited_courses.append({
                'course_code': course.code,
                'course_name': course.name,
                'credits': 4, # Default standard credits
                'grade': 'Awaited',
                'grade_points': '-',
            })
            
    # Determine ongoing semester number
    ongoing_semester = (latest_result.semester + 1) if latest_result else 1
    # Check if any graded courses belong to the highest semester, but we don't strictly bind Course to Semester in the model.
    # To be safe, if there's a SemesterResult for ongoing_semester already (happens if some grades published), 
    # we would ideally merge it, but for simplicity we can just render an "Ongoing Semester" block in the template.

    context = {
        'results': results,
        'cgpa': cgpa,
        'total_credits': total_credits,
        'latest_semester': latest_result.semester if latest_result else 0,
        'awaited_courses': awaited_courses,
        'ongoing_semester': ongoing_semester
    }
    
    return render(request, 'results/student_results.html', context)

@login_required
def academic_hub(request):
    if request.user.role != 'FACULTY':
        messages.error(request, "Only faculty can access the Academic Hub.")
        return redirect('dashboard')
    
    my_courses = Course.objects.filter(faculty=request.user).annotate(
        student_count=Count('students'),
        avg_grade_points=Avg('course_grades__grade_points')
    )
    
    context = {
        'courses': my_courses,
    }
    return render(request, 'results/academic_hub.html', context)

@login_required
def manage_grades(request, course_id):
    if request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    
    # Level 1: Faculty views Sections assigned to this course
    # Get sections containing students enrolled in this course
    sections = Section.objects.filter(members__enrolled_courses=course).distinct()
    
    context = {
        'course': course,
        'sections': sections,
    }
    return render(request, 'results/manage_grades.html', context)


@login_required
def manage_section_exams(request, course_id, section_id):
    if request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    section = get_object_or_404(Section, id=section_id)
    
    # Ensure Exams exist for this course + section
    from .models import Exam
    required_exams = [
        ('CA1', 'CA 1', 30),
        ('CA2', 'CA 2', 30),
        ('CA3', 'CA 3', 30),
        ('MID', 'Mid Term', 30),
        ('END', 'End Term', 60),
    ]
    
    for ex_type, name, max_m in required_exams:
        Exam.objects.get_or_create(
            course=course,
            section=section,
            exam_type=ex_type,
            defaults={'max_marks': max_m}
        )
        
    exams = Exam.objects.filter(course=course, section=section)
    from .models import CourseGrade
    published_grades = CourseGrade.objects.filter(course=course, student__section=section).select_related('student').order_by('student__username')
    
    context = {
        'course': course,
        'section': section,
        'exams': exams,
        'published_grades': published_grades,
    }
    return render(request, 'results/manage_section_exams.html', context)


@login_required
def manage_exam_marks(request, course_id, section_id, exam_id):
    if request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    section = get_object_or_404(Section, id=section_id)
    from .models import Exam, StudentExamMark
    
    exam = get_object_or_404(Exam, id=exam_id, course=course, section=section)
    students = course.students.filter(section=section).order_by('username')
    
    if request.method == 'POST':
        for student in students:
            mark_key = f'mark_{student.id}'
            if mark_key in request.POST and request.POST[mark_key].strip() != '':
                try:
                    mark_val = decimal.Decimal(request.POST[mark_key])
                    # Ensure marks do not exceed maximum marks
                    if mark_val > exam.max_marks:
                        mark_val = decimal.Decimal(exam.max_marks)
                    elif mark_val < 0:
                        mark_val = decimal.Decimal(0)
                        
                    StudentExamMark.objects.update_or_create(
                        exam=exam,
                        student=student,
                        defaults={'marks_obtained': mark_val}
                    )
                except (ValueError, decimal.InvalidOperation):
                    continue
        messages.success(request, f"Marks updated successfully for {exam.get_exam_type_display()}")
        return redirect('manage_section_exams', course_id=course.id, section_id=section.id)

    # Prepare data for template
    existing_marks = StudentExamMark.objects.filter(exam=exam).select_related('student')
    marks_map = {m.student_id: m for m in existing_marks}
    
    student_data = []
    for student in students:
        student_data.append({
            'student': student,
            'mark_obj': marks_map.get(student.id)
        })
        
    context = {
        'course': course,
        'section': section,
        'exam': exam,
        'student_data': student_data,
    }
    return render(request, 'results/manage_exam_marks.html', context)


@login_required
def calculate_final_grades(request, course_id, section_id):
    if request.method != 'POST' or request.user.role != 'FACULTY':
        return redirect('dashboard')
        
    course = get_object_or_404(Course, id=course_id, faculty=request.user)
    section = get_object_or_404(Section, id=section_id)
    
    from .models import Exam, StudentExamMark, CourseGrade, SemesterResult
    from attendance.models import AttendanceSession, AttendanceRecord
    
    # Fetch ALL students and ALL exams for the course to calculate a campus-wide curve
    all_students = course.students.all()
    all_exams = Exam.objects.filter(course=course)
    
    # Pre-fetch marks
    all_marks = StudentExamMark.objects.filter(exam__in=all_exams).select_related('exam', 'student')
    
    # Calculate attendance total possible for this course (or overall)
    total_sessions = AttendanceSession.objects.filter(course=course).count()
    
    student_net_marks = []
    
    for student in all_students:
        # 1. Total of 3 CAs (Out of 30 each) -> Combined up to 90. Weightage 25% => (Marks/90) * 25
        ca1_marks = decimal.Decimal('0.0')
        ca2_marks = decimal.Decimal('0.0')
        ca3_marks = decimal.Decimal('0.0')
        ca_marks = decimal.Decimal('0.0')
        max_ca = decimal.Decimal('90.0')
        
        # 2. Mid Term (Out of 30). Weightage 20% => (Marks/30) * 20
        mid_marks = decimal.Decimal('0.0')
        max_mid = decimal.Decimal('30.0')
        
        # 3. End Term (Out of 60). Weightage 50% => (Marks/60) * 50
        end_marks = decimal.Decimal('0.0')
        max_end = decimal.Decimal('60.0')
        
        for mark in all_marks:
            if mark.student_id == student.id:
                if mark.exam.exam_type == 'CA1':
                    ca1_marks += mark.marks_obtained
                elif mark.exam.exam_type == 'CA2':
                    ca2_marks += mark.marks_obtained
                elif mark.exam.exam_type == 'CA3':
                    ca3_marks += mark.marks_obtained
                
                if mark.exam.exam_type.startswith('CA'):
                    ca_marks += mark.marks_obtained
                elif mark.exam.exam_type == 'MID':
                    mid_marks += mark.marks_obtained
                elif mark.exam.exam_type == 'END':
                    end_marks += mark.marks_obtained
                    
        # Calculate weighted components
        ca_component = (ca_marks / max_ca) * decimal.Decimal('25') if max_ca > 0 else decimal.Decimal('0')
        mid_component = (mid_marks / max_mid) * decimal.Decimal('20') if max_mid > 0 else decimal.Decimal('0')
        end_component = (end_marks / max_end) * decimal.Decimal('50') if max_end > 0 else decimal.Decimal('0')
        
        # 4. Attendance component (5%)
        # Proportional calculation based on attendance percentage
        att_component = decimal.Decimal('0.0')
        if total_sessions > 0:
            present_count = AttendanceRecord.objects.filter(student=student, session__course=course, is_present=True).count()
            att_percentage = (decimal.Decimal(present_count) / decimal.Decimal(total_sessions)) * 100
            # Full 5 marks only for 100% attendance, scales down proportionally
            att_component = (att_percentage / decimal.Decimal('100.0')) * decimal.Decimal('5')
            
        net_marks = ca_component + mid_component + end_component + att_component
        student_net_marks.append((student, net_marks, {
            'ca1': ca1_marks, 'ca2': ca2_marks, 'ca3': ca3_marks,
            'mid': mid_marks, 'end': end_marks,
            'ca_w': ca_component, 'mid_w': mid_component, 'end_w': end_component, 'att_w': att_component
        }))
    # Calculate relative grades based on net_marks
    if not student_net_marks:
        messages.warning(request, "No students found to evaluate.")
        return redirect('manage_section_exams', course_id=course.id, section_id=section.id)
        
    # Sort students by net_marks descending to find percentiles
    student_net_marks.sort(key=lambda x: x[1], reverse=True)
    total_students = len(student_net_marks)
    
    course_credits = 4  # Default
    
    for rank, (student, net_mark, comps) in enumerate(student_net_marks, start=1):
        # Calculate percentile (number of people you scored better than or equal to, divided by total)
        percentile = ((total_students - rank + 1) / total_students) * 100
        
        # Assign Grade Based on Percentile (Relative Grading)
        if net_mark < 40:
            grade_letter = 'E'
            grade_points = 0
        elif percentile >= 90:
            grade_letter = 'O'
            grade_points = 10
        elif percentile >= 80:
            grade_letter = 'A+'
            grade_points = 9
        elif percentile >= 70:
            grade_letter = 'A'
            grade_points = 8
        elif percentile >= 55:
            grade_letter = 'B+'
            grade_points = 7
        elif percentile >= 40:
            grade_letter = 'B'
            grade_points = 6
        elif percentile >= 25:
            grade_letter = 'C'
            grade_points = 5
        elif percentile >= 10:
            grade_letter = 'D'
            grade_points = 4
        else:
            # Bottom 10%, but they passed the 40 limit, so they get the lowest passing grade
            grade_letter = 'D'
            grade_points = 4
            
        # Only publish grades for the students in the section managed by this faculty
        if student.section != section:
            continue
            
        # Update or create course grade
        sem_result, _ = SemesterResult.objects.get_or_create(
            student=student,
            semester=1, # Mock default
            defaults={'sgpa': 0, 'cgpa': 0, 'credits_earned': 0, 'total_credits': 0}
        )
        
        grade_obj, created = CourseGrade.objects.update_or_create(
            semester_result=sem_result,
            course=course,
            student=student,
            defaults={
                'course_name': course.name,
                'course_code': course.code,
                'grade': grade_letter,
                'grade_points': grade_points,
                'credits': course_credits,
                'net_marks': net_mark,
                'ca1_marks': comps['ca1'],
                'ca2_marks': comps['ca2'],
                'ca3_marks': comps['ca3'],
                'mid_marks': comps['mid'],
                'end_marks': comps['end'],
                'ca_weighted': comps['ca_w'],
                'mid_weighted': comps['mid_w'],
                'end_weighted': comps['end_w'],
                'att_weighted': comps['att_w']
            }
        )
        
        # Recalculate SGPA
        all_grades = sem_result.grades.all()
        total_pts = sum(g.grade_points * g.credits for g in all_grades)
        total_creds = sum(g.credits for g in all_grades)
        
        if total_creds > 0:
            sem_result.sgpa = decimal.Decimal(total_pts) / decimal.Decimal(total_creds)
            sem_result.total_credits = total_creds
            sem_result.credits_earned = sum(g.credits for g in all_grades if g.grade != 'E')
            sem_result.save()
            
            # Recalculate CGPA properly across all semesters up to this one
            all_sems = SemesterResult.objects.filter(student=student, semester__lte=sem_result.semester).prefetch_related('grades')
            cum_pts = sum(sum(g.grade_points * g.credits for g in sr.grades.all()) for sr in all_sems)
            cum_creds = sum(sr.total_credits for sr in all_sems)
            
            if cum_creds > 0:
                sem_result.cgpa = decimal.Decimal(cum_pts) / decimal.Decimal(cum_creds)
            else:
                sem_result.cgpa = sem_result.sgpa
                
            sem_result.save()
            
    messages.success(request, f"Final grades calculated and published successfully for {course.code} - {section.name}")
    return redirect('manage_section_exams', course_id=course.id, section_id=section.id)
