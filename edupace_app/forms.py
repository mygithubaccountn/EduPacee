from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    Course, Teacher, Student, AcademicBoard,
    ProgramOutcome, LearningOutcome, Grade
)


class RoleLoginForm(AuthenticationForm):
    """Login form with role selection"""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
        ('academic_board', 'Academic Board'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username'
        })
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class CourseForm(forms.ModelForm):
    """Form for creating/editing courses (Academic Board only)"""
    class Meta:
        model = Course
        fields = ['code', 'name', 'description', 'credits', 'is_locked']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'is_locked': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProgramOutcomeForm(forms.ModelForm):
    """Form for creating/editing program outcomes"""
    class Meta:
        model = ProgramOutcome
        fields = ['code', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LearningOutcomeForm(forms.ModelForm):
    """Form for creating/editing learning outcomes"""
    class Meta:
        model = LearningOutcome
        fields = ['code', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class GradeUploadForm(forms.Form):
    """Form for uploading Excel file with grades"""
    excel_file = forms.FileField(
        label='Excel File',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        }),
        help_text='Upload an Excel file (.xlsx or .xls) containing student grades'
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select a course'
    )
    semester = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Fall 2024'
        })
    )
    academic_year = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2024-2025'
        })
    )
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = teacher.courses.all()


class GradeForm(forms.ModelForm):
    """Form for manually entering grades"""
    class Meta:
        model = Grade
        fields = ['student', 'course', 'grade', 'percentage', 'semester', 'academic_year']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'course': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': 0.01
            }),
            'semester': forms.TextInput(attrs={'class': 'form-control'}),
            'academic_year': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        teacher = kwargs.pop('teacher', None)
        super().__init__(*args, **kwargs)
        if teacher:
            self.fields['course'].queryset = teacher.courses.all()


class AssignTeacherToCourseForm(forms.Form):
    """Form for assigning teachers to courses"""
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Select a teacher'
    )

