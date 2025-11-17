from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from functools import wraps
from .models import Teacher, Student, AcademicBoard


def get_user_role(user):
    """Get the role of a user"""
    if not user.is_authenticated:
        return None
    
    if hasattr(user, 'teacher_profile'):
        return 'teacher'
    elif hasattr(user, 'student_profile'):
        return 'student'
    elif hasattr(user, 'academic_board_profile'):
        return 'academic_board'
    return None


def get_user_profile(user):
    """Get the profile object for a user based on their role"""
    role = get_user_role(user)
    if role == 'teacher':
        return user.teacher_profile
    elif role == 'student':
        return user.student_profile
    elif role == 'academic_board':
        return user.academic_board_profile
    return None


def role_required(*allowed_roles):
    """Decorator to check if user has required role"""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('edupace_app:login')
            
            user_role = get_user_role(request.user)
            if user_role not in allowed_roles:
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('edupace_app:dashboard_redirect')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def check_course_edit_permission(user, course):
    """Check if user can edit a course (Academic Board only, and only if not locked)"""
    if get_user_role(user) != 'academic_board':
        return False
    return not course.is_locked


def check_learning_outcome_permission(user, course):
    """Check if user can add learning outcomes (Teacher only, and only if course is not locked)"""
    if get_user_role(user) != 'teacher':
        return False
    
    try:
        teacher = user.teacher_profile
        if course not in teacher.courses.all():
            return False
    except Teacher.DoesNotExist:
        return False
    
    return not course.is_locked


def check_grade_permission(user, course):
    """Check if user can add grades (Teacher only, and only if course is not locked)"""
    return check_learning_outcome_permission(user, course)


def excel_to_pdf(excel_file_path, output_pdf_path):
    """
    Convert Excel file to PDF
    Requires: openpyxl, reportlab, pandas
    """
    try:
        import pandas as pd
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        
        # Read Excel file
        df = pd.read_excel(excel_file_path)
        
        # Create PDF
        doc = SimpleDocTemplate(output_pdf_path, pagesize=A4)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceAfter=30,
        )
        
        # Add title
        title = Paragraph("Grade Report", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.2*inch))
        
        # Convert DataFrame to list of lists for table
        data = [df.columns.tolist()] + df.values.tolist()
        
        # Create table
        table = Table(data)
        
        # Style the table
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(table)
        
        # Build PDF
        doc.build(elements)
        return True
        
    except Exception as e:
        print(f"Error converting Excel to PDF: {str(e)}")
        return False


def process_excel_grades(excel_file, course, semester='', academic_year='', created_by=None):
    """
    Process Excel file and create Grade objects
    Expected Excel format:
    - First row: headers (Student ID, Grade, Percentage)
    - Subsequent rows: data
    """
    try:
        import pandas as pd
        from .models import Student, Grade
        
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        # Expected columns (case-insensitive)
        df.columns = df.columns.str.strip().str.lower()
        
        # Map common column names
        student_id_col = None
        grade_col = None
        percentage_col = None
        
        for col in df.columns:
            if 'student' in col and 'id' in col:
                student_id_col = col
            elif 'grade' in col:
                grade_col = col
            elif 'percentage' in col or 'percent' in col:
                percentage_col = col
        
        if not student_id_col or not grade_col:
            return False, "Excel file must contain 'Student ID' and 'Grade' columns"
        
        grades_created = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                student_id = str(row[student_id_col]).strip()
                grade_value = str(row[grade_col]).strip().upper()
                percentage = None
                
                if percentage_col and pd.notna(row.get(percentage_col)):
                    percentage = float(row[percentage_col])
                
                # Get student
                try:
                    student = Student.objects.get(student_id=student_id)
                except Student.DoesNotExist:
                    errors.append(f"Student with ID {student_id} not found (row {index + 2})")
                    continue
                
                # Validate grade
                valid_grades = [choice[0] for choice in Grade.GRADE_CHOICES]
                if grade_value not in valid_grades:
                    errors.append(f"Invalid grade '{grade_value}' for student {student_id} (row {index + 2})")
                    continue
                
                # Create or update grade
                grade, created = Grade.objects.update_or_create(
                    student=student,
                    course=course,
                    semester=semester,
                    academic_year=academic_year,
                    defaults={
                        'grade': grade_value,
                        'percentage': percentage,
                        'created_by': created_by,
                    }
                )
                
                if created:
                    grades_created += 1
                    
            except Exception as e:
                errors.append(f"Error processing row {index + 2}: {str(e)}")
                continue
        
        message = f"Successfully created/updated {grades_created} grade(s)."
        if errors:
            message += f" {len(errors)} error(s) occurred."
        
        return True, message, errors
        
    except Exception as e:
        return False, f"Error processing Excel file: {str(e)}", []

