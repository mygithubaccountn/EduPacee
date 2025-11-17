from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import HttpResponse, JsonResponse, FileResponse
from django.core.exceptions import PermissionDenied
from django.db.models import Q
import os
import tempfile

from .models import (
    Course, Teacher, Student, AcademicBoard,
    ProgramOutcome, LearningOutcome, Grade
)
from .forms import (
    RoleLoginForm, CourseForm, ProgramOutcomeForm,
    LearningOutcomeForm, GradeUploadForm, GradeForm, AssignTeacherToCourseForm
)
from .utils import (
    get_user_role, get_user_profile, role_required,
    check_course_edit_permission, check_learning_outcome_permission,
    check_grade_permission, excel_to_pdf, process_excel_grades
)


def login_view(request):
    """Login view with role selection"""
    if request.user.is_authenticated:
        return redirect('edupace_app:dashboard_redirect')
    
    if request.method == 'POST':
        form = RoleLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            role = form.cleaned_data.get('role')
            
            # Verify user has the selected role
            user_role = get_user_role(user)
            if user_role != role:
                messages.error(request, f'This account is not registered as a {role.title()}.')
                return render(request, 'edupace_app/login.html', {'form': form})
            
            login(request, user)
            messages.success(request, f'Welcome, {user.get_full_name() or user.username}!')
            return redirect('edupace_app:dashboard_redirect')
    else:
        form = RoleLoginForm()
    
    return render(request, 'edupace_app/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('edupace_app:login')


@login_required
def dashboard_redirect(request):
    """Redirect user to their role-specific dashboard"""
    role = get_user_role(request.user)
    
    if role == 'student':
        return redirect('edupace_app:student_dashboard')
    elif role == 'teacher':
        return redirect('edupace_app:teacher_dashboard')
    elif role == 'academic_board':
        return redirect('edupace_app:academic_board_dashboard')
    else:
        messages.error(request, 'Your account is not associated with any role.')
        return redirect('edupace_app:login')


# ==================== STUDENT VIEWS ====================

@login_required
@role_required('student')
def student_dashboard(request):
    """Student dashboard - view grades, program outcomes, learning outcomes"""
    student = get_user_profile(request.user)
    courses = student.courses.all()
    grades = Grade.objects.filter(student=student).select_related('course')
    
    context = {
        'student': student,
        'courses': courses,
        'grades': grades,
    }
    return render(request, 'edupace_app/student/dashboard.html', context)


@login_required
@role_required('student')
def student_course_detail(request, course_id):
    """Student view of a specific course"""
    student = get_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    # Check if student is enrolled
    if course not in student.courses.all():
        messages.error(request, 'You are not enrolled in this course.')
        return redirect('edupace_app:student_dashboard')
    
    grade = Grade.objects.filter(student=student, course=course).first()
    program_outcomes = course.program_outcomes.all()
    learning_outcomes = course.learning_outcomes.all()
    
    context = {
        'course': course,
        'grade': grade,
        'program_outcomes': program_outcomes,
        'learning_outcomes': learning_outcomes,
    }
    return render(request, 'edupace_app/student/course_detail.html', context)


# ==================== TEACHER VIEWS ====================

@login_required
@role_required('teacher')
def teacher_dashboard(request):
    """Teacher dashboard"""
    teacher = get_user_profile(request.user)
    courses = teacher.courses.all()
    
    # Get statistics
    total_courses = courses.count()
    courses_with_los = courses.filter(learning_outcomes__isnull=False).distinct().count()
    
    context = {
        'teacher': teacher,
        'courses': courses,
        'total_courses': total_courses,
        'courses_with_los': courses_with_los,
    }
    return render(request, 'edupace_app/teacher/dashboard.html', context)


@login_required
@role_required('teacher')
def teacher_course_detail(request, course_id):
    """Teacher view of a specific course"""
    teacher = get_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    # Check if teacher teaches this course
    if course not in teacher.courses.all():
        messages.error(request, 'You do not teach this course.')
        return redirect('edupace_app:teacher_dashboard')
    
    learning_outcomes = course.learning_outcomes.all()
    program_outcomes = course.program_outcomes.all()
    grades = Grade.objects.filter(course=course).select_related('student')
    
    context = {
        'course': course,
        'learning_outcomes': learning_outcomes,
        'program_outcomes': program_outcomes,
        'grades': grades,
        'can_edit': not course.is_locked,
    }
    return render(request, 'edupace_app/teacher/course_detail.html', context)


@login_required
@role_required('teacher')
def add_learning_outcome(request, course_id):
    """Add learning outcome to a course"""
    teacher = get_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if not check_learning_outcome_permission(request.user, course):
        messages.error(request, 'You cannot add learning outcomes to this course.')
        return redirect('edupace_app:teacher_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = LearningOutcomeForm(request.POST)
        if form.is_valid():
            learning_outcome = form.save(commit=False)
            learning_outcome.course = course
            learning_outcome.created_by = request.user
            learning_outcome.save()
            messages.success(request, f'Learning outcome {learning_outcome.code} added successfully.')
            return redirect('edupace_app:teacher_course_detail', course_id=course_id)
    else:
        form = LearningOutcomeForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'edupace_app/teacher/add_learning_outcome.html', context)


@login_required
@role_required('teacher')
def edit_learning_outcome(request, lo_id):
    """Edit a learning outcome"""
    learning_outcome = get_object_or_404(LearningOutcome, id=lo_id)
    teacher = get_user_profile(request.user)
    
    # Check permissions
    if learning_outcome.course not in teacher.courses.all():
        messages.error(request, 'You do not have permission to edit this learning outcome.')
        return redirect('edupace_app:teacher_dashboard')
    
    if learning_outcome.course.is_locked:
        messages.error(request, 'This course is locked. You cannot edit learning outcomes.')
        return redirect('edupace_app:teacher_course_detail', course_id=learning_outcome.course.id)
    
    if request.method == 'POST':
        form = LearningOutcomeForm(request.POST, instance=learning_outcome)
        if form.is_valid():
            form.save()
            messages.success(request, 'Learning outcome updated successfully.')
            return redirect('edupace_app:teacher_course_detail', course_id=learning_outcome.course.id)
    else:
        form = LearningOutcomeForm(instance=learning_outcome)
    
    context = {
        'form': form,
        'learning_outcome': learning_outcome,
        'course': learning_outcome.course,
    }
    return render(request, 'edupace_app/teacher/edit_learning_outcome.html', context)


@login_required
@role_required('teacher')
def delete_learning_outcome(request, lo_id):
    """Delete a learning outcome"""
    learning_outcome = get_object_or_404(LearningOutcome, id=lo_id)
    teacher = get_user_profile(request.user)
    course = learning_outcome.course
    
    # Check permissions
    if course not in teacher.courses.all():
        messages.error(request, 'You do not have permission to delete this learning outcome.')
        return redirect('edupace_app:teacher_dashboard')
    
    if course.is_locked:
        messages.error(request, 'This course is locked. You cannot delete learning outcomes.')
        return redirect('edupace_app:teacher_course_detail', course_id=course.id)
    
    if request.method == 'POST':
        learning_outcome.delete()
        messages.success(request, 'Learning outcome deleted successfully.')
        return redirect('edupace_app:teacher_course_detail', course_id=course.id)
    
    context = {
        'learning_outcome': learning_outcome,
        'course': course,
    }
    return render(request, 'edupace_app/teacher/delete_learning_outcome.html', context)


@login_required
@role_required('teacher')
def upload_grades(request, course_id):
    """Upload grades via Excel file"""
    teacher = get_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    # Check permissions
    if not check_grade_permission(request.user, course):
        messages.error(request, 'You cannot upload grades for this course.')
        return redirect('edupace_app:teacher_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = GradeUploadForm(request.POST, request.FILES, teacher=teacher)
        if form.is_valid():
            excel_file = form.cleaned_data['excel_file']
            semester = form.cleaned_data.get('semester', '')
            academic_year = form.cleaned_data.get('academic_year', '')
            
            # Process Excel file
            success, message, errors = process_excel_grades(
                excel_file, course, semester, academic_year, request.user
            )
            
            if success:
                messages.success(request, message)
                if errors:
                    for error in errors[:10]:  # Show first 10 errors
                        messages.warning(request, error)
            else:
                messages.error(request, message)
            
            return redirect('edupace_app:teacher_course_detail', course_id=course_id)
    else:
        form = GradeUploadForm(teacher=teacher, initial={'course': course})
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'edupace_app/teacher/upload_grades.html', context)


@login_required
@role_required('teacher')
def convert_grades_to_pdf(request, course_id):
    """Convert grades Excel to PDF"""
    teacher = get_user_profile(request.user)
    course = get_object_or_404(Course, id=course_id)
    
    if course not in teacher.courses.all():
        messages.error(request, 'You do not teach this course.')
        return redirect('edupace_app:teacher_dashboard')
    
    grades = Grade.objects.filter(course=course).select_related('student')
    
    if not grades.exists():
        messages.error(request, 'No grades found for this course.')
        return redirect('edupace_app:teacher_course_detail', course_id=course_id)
    
    # Create temporary Excel file
    try:
        import pandas as pd
        
        data = []
        for grade in grades:
            data.append({
                'Student ID': grade.student.student_id,
                'Student Name': grade.student.user.get_full_name() or grade.student.user.username,
                'Grade': grade.grade,
                'Percentage': grade.percentage or '',
                'Semester': grade.semester or '',
                'Academic Year': grade.academic_year or '',
            })
        
        df = pd.DataFrame(data)
        
        # Create temporary files
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_excel:
            df.to_excel(tmp_excel.name, index=False)
            excel_path = tmp_excel.name
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_pdf:
            pdf_path = tmp_pdf.name
        
        # Convert to PDF
        if excel_to_pdf(excel_path, pdf_path):
            response = FileResponse(
                open(pdf_path, 'rb'),
                content_type='application/pdf',
                filename=f'{course.code}_grades.pdf'
            )
            # Clean up
            os.unlink(excel_path)
            return response
        else:
            messages.error(request, 'Error converting grades to PDF.')
            os.unlink(excel_path)
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
            return redirect('edupace_app:teacher_course_detail', course_id=course_id)
            
    except Exception as e:
        messages.error(request, f'Error generating PDF: {str(e)}')
        return redirect('edupace_app:teacher_course_detail', course_id=course_id)


# ==================== ACADEMIC BOARD VIEWS ====================

@login_required
@role_required('academic_board')
def academic_board_dashboard(request):
    """Academic Board dashboard"""
    courses = Course.objects.all()
    total_courses = courses.count()
    locked_courses = courses.filter(is_locked=True).count()
    active_courses = total_courses - locked_courses
    
    context = {
        'courses': courses,
        'total_courses': total_courses,
        'locked_courses': locked_courses,
        'active_courses': active_courses,
    }
    return render(request, 'edupace_app/academic_board/dashboard.html', context)


@login_required
@role_required('academic_board')
def create_course(request):
    """Create a new course"""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save()
            messages.success(request, f'Course {course.code} created successfully.')
            return redirect('edupace_app:academic_board_course_detail', course_id=course.id)
    else:
        form = CourseForm()
    
    return render(request, 'edupace_app/academic_board/create_course.html', {'form': form})


@login_required
@role_required('academic_board')
def academic_board_course_detail(request, course_id):
    """Academic Board view of a specific course"""
    course = get_object_or_404(Course, id=course_id)
    program_outcomes = course.program_outcomes.all()
    learning_outcomes = course.learning_outcomes.all()
    teachers = course.teachers.all()
    students = course.students.all()
    grades = Grade.objects.filter(course=course).select_related('student')
    
    context = {
        'course': course,
        'program_outcomes': program_outcomes,
        'learning_outcomes': learning_outcomes,
        'teachers': teachers,
        'students': students,
        'grades': grades,
        'can_edit': not course.is_locked,
    }
    return render(request, 'edupace_app/academic_board/course_detail.html', context)


@login_required
@role_required('academic_board')
def edit_course(request, course_id):
    """Edit a course"""
    course = get_object_or_404(Course, id=course_id)
    
    # Check if course can be edited
    if not check_course_edit_permission(request.user, course):
        messages.error(request, 'This course is locked and cannot be edited.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course updated successfully.')
            return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    else:
        form = CourseForm(instance=course)
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'edupace_app/academic_board/edit_course.html', context)


@login_required
@role_required('academic_board')
def delete_course(request, course_id):
    """Delete a course"""
    course = get_object_or_404(Course, id=course_id)
    
    if not check_course_edit_permission(request.user, course):
        messages.error(request, 'This course is locked and cannot be deleted.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        course_code = course.code
        course.delete()
        messages.success(request, f'Course {course_code} deleted successfully.')
        return redirect('edupace_app:academic_board_dashboard')
    
    return render(request, 'edupace_app/academic_board/delete_course.html', {'course': course})


@login_required
@role_required('academic_board')
def add_program_outcome(request, course_id):
    """Add program outcome to a course"""
    course = get_object_or_404(Course, id=course_id)
    
    if not check_course_edit_permission(request.user, course):
        messages.error(request, 'This course is locked. You cannot add program outcomes.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = ProgramOutcomeForm(request.POST)
        if form.is_valid():
            program_outcome = form.save(commit=False)
            program_outcome.course = course
            program_outcome.created_by = request.user
            program_outcome.save()
            messages.success(request, f'Program outcome {program_outcome.code} added successfully.')
            return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    else:
        form = ProgramOutcomeForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'edupace_app/academic_board/add_program_outcome.html', context)


@login_required
@role_required('academic_board')
def edit_program_outcome(request, po_id):
    """Edit a program outcome"""
    program_outcome = get_object_or_404(ProgramOutcome, id=po_id)
    course = program_outcome.course
    
    if not check_course_edit_permission(request.user, course):
        messages.error(request, 'This course is locked. You cannot edit program outcomes.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course.id)
    
    if request.method == 'POST':
        form = ProgramOutcomeForm(request.POST, instance=program_outcome)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program outcome updated successfully.')
            return redirect('edupace_app:academic_board_course_detail', course_id=course.id)
    else:
        form = ProgramOutcomeForm(instance=program_outcome)
    
    context = {
        'form': form,
        'program_outcome': program_outcome,
        'course': course,
    }
    return render(request, 'edupace_app/academic_board/edit_program_outcome.html', context)


@login_required
@role_required('academic_board')
def delete_program_outcome(request, po_id):
    """Delete a program outcome"""
    program_outcome = get_object_or_404(ProgramOutcome, id=po_id)
    course = program_outcome.course
    
    if not check_course_edit_permission(request.user, course):
        messages.error(request, 'This course is locked. You cannot delete program outcomes.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course.id)
    
    if request.method == 'POST':
        program_outcome.delete()
        messages.success(request, 'Program outcome deleted successfully.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course.id)
    
    context = {
        'program_outcome': program_outcome,
        'course': course,
    }
    return render(request, 'edupace_app/academic_board/delete_program_outcome.html', context)


@login_required
@role_required('academic_board')
def assign_teacher_to_course(request, course_id):
    """Assign a teacher to a course"""
    course = get_object_or_404(Course, id=course_id)
    
    if not check_course_edit_permission(request.user, course):
        messages.error(request, 'This course is locked. You cannot assign teachers.')
        return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    
    if request.method == 'POST':
        form = AssignTeacherToCourseForm(request.POST)
        if form.is_valid():
            teacher = form.cleaned_data['teacher']
            course.teachers.add(teacher)
            messages.success(request, f'Teacher {teacher.user.get_full_name()} assigned to course.')
            return redirect('edupace_app:academic_board_course_detail', course_id=course_id)
    else:
        form = AssignTeacherToCourseForm()
    
    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'edupace_app/academic_board/assign_teacher.html', context)
