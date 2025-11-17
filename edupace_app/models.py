from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Course(models.Model):
    """Course model representing a course in the system"""
    code = models.CharField(max_length=20, unique=True, help_text="Course code (e.g., CS101)")
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    credits = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(10)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(
        default=False,
        help_text="If True, teachers cannot add learning outcomes or grades"
    )
    
    class Meta:
        ordering = ['code']
        verbose_name = "Course"
        verbose_name_plural = "Courses"
    
    def __str__(self):
        return f"{self.code} - {self.name}"


class Teacher(models.Model):
    """Teacher model extending User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100, blank=True)
    courses = models.ManyToManyField(Course, related_name='teachers', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Teacher"
        verbose_name_plural = "Teachers"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class Student(models.Model):
    """Student model extending User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    enrollment_date = models.DateField()
    program = models.CharField(max_length=100, blank=True)
    courses = models.ManyToManyField(Course, related_name='students', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Student"
        verbose_name_plural = "Students"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"


class AcademicBoard(models.Model):
    """Academic Board member model extending User"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='academic_board_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    designation = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Academic Board Member"
        verbose_name_plural = "Academic Board Members"
    
    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"


class ProgramOutcome(models.Model):
    """Program outcomes for courses"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='program_outcomes')
    code = models.CharField(max_length=20, help_text="PO code (e.g., PO1, PO2)")
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_program_outcomes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'code']
        ordering = ['course', 'code']
        verbose_name = "Program Outcome"
        verbose_name_plural = "Program Outcomes"
    
    def __str__(self):
        return f"{self.course.code} - {self.code}"


class LearningOutcome(models.Model):
    """Learning outcomes for courses"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_outcomes')
    code = models.CharField(max_length=20, help_text="LO code (e.g., LO1, LO2)")
    description = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_learning_outcomes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['course', 'code']
        ordering = ['course', 'code']
        verbose_name = "Learning Outcome"
        verbose_name_plural = "Learning Outcomes"
    
    def __str__(self):
        return f"{self.course.code} - {self.code}"


class Grade(models.Model):
    """Grade model for student course grades"""
    GRADE_CHOICES = [
        ('A+', 'A+'),
        ('A', 'A'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B', 'B'),
        ('B-', 'B-'),
        ('C+', 'C+'),
        ('C', 'C'),
        ('C-', 'C-'),
        ('D', 'D'),
        ('F', 'F'),
    ]
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='grades')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='grades')
    grade = models.CharField(max_length=2, choices=GRADE_CHOICES)
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    semester = models.CharField(max_length=20, blank=True)
    academic_year = models.CharField(max_length=20, blank=True)
    uploaded_file = models.FileField(upload_to='grade_files/', null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_grades')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student', 'course', 'semester', 'academic_year']
        ordering = ['-academic_year', '-semester', 'course']
        verbose_name = "Grade"
        verbose_name_plural = "Grades"
    
    def __str__(self):
        return f"{self.student.student_id} - {self.course.code} - {self.grade}"
