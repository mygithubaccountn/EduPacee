from django.contrib import admin
from .models import (
    Course, Teacher, Student, AcademicBoard,
    ProgramOutcome, LearningOutcome, Grade
)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'credits', 'is_locked', 'created_at']
    list_filter = ['is_locked', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'department', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    filter_horizontal = ['courses']
    readonly_fields = ['created_at']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_id', 'program', 'enrollment_date', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'student_id']
    filter_horizontal = ['courses']
    readonly_fields = ['created_at']


@admin.register(AcademicBoard)
class AcademicBoardAdmin(admin.ModelAdmin):
    list_display = ['user', 'employee_id', 'designation', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'employee_id']
    readonly_fields = ['created_at']


@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ['code', 'course', 'created_by', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['code', 'description', 'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ['code', 'course', 'created_by', 'created_at']
    list_filter = ['course', 'created_at']
    search_fields = ['code', 'description', 'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'grade', 'percentage', 'semester', 'academic_year', 'created_at']
    list_filter = ['grade', 'course', 'semester', 'academic_year', 'created_at']
    search_fields = ['student__student_id', 'student__user__username', 'course__code', 'course__name']
    readonly_fields = ['created_at', 'updated_at']
