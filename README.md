# EduPace - Academic Management Platform

EduPace is a comprehensive Django-based platform for managing academic courses, grades, learning outcomes, and program outcomes. It supports three distinct user roles: Students, Teachers, and Academic Board members.

## Features

### Role-Based Access Control
- **Students**: View their grades, program outcomes, and learning outcomes
- **Teachers**: Add learning outcomes and upload grades for courses they teach
- **Academic Board**: Create courses, set program outcomes, and manage course settings

### Key Functionality
- Course management with locking mechanism
- Learning outcomes and program outcomes tracking
- Excel-based grade upload with automatic processing
- Excel to PDF conversion for grade reports
- Role-specific dashboards
- Comprehensive permission system

## Installation

### Prerequisites
- Python 3.8+
- Django 5.2+
- Required packages (see requirements below)

### Setup Steps

1. **Activate your virtual environment** (if using one):
   ```bash
   source venv/bin/activate  # On macOS/Linux
   # or
   venv\Scripts\activate  # On Windows
   ```

2. **Install required packages**:
   ```bash
   pip install django openpyxl pandas reportlab pillow
   ```

3. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Create a superuser** (for Django admin):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**:
   ```bash
   python manage.py runserver
   ```

6. **Access the application**:
   - Main application: http://127.0.0.1:8000/
   - Admin panel: http://127.0.0.1:8000/admin/

## Creating Users and Profiles

### Option 1: Using Django Admin

1. Log in to the admin panel at `/admin/`
2. Create a User (Django's built-in User model)
3. Create the corresponding profile:
   - **Student**: Create a Student profile linked to the User
   - **Teacher**: Create a Teacher profile linked to the User
   - **Academic Board**: Create an AcademicBoard profile linked to the User

### Option 2: Using Django Shell

```python
from django.contrib.auth.models import User
from edupace_app.models import Student, Teacher, AcademicBoard, Course

# Create a student
user = User.objects.create_user(username='student1', password='password123', 
                                first_name='John', last_name='Doe')
student = Student.objects.create(user=user, student_id='STU001', 
                                  enrollment_date='2024-01-01', program='Computer Science')

# Create a teacher
user = User.objects.create_user(username='teacher1', password='password123',
                                first_name='Jane', last_name='Smith')
teacher = Teacher.objects.create(user=user, employee_id='TCH001', department='CS')

# Create an academic board member
user = User.objects.create_user(username='board1', password='password123',
                                first_name='Admin', last_name='User')
board = AcademicBoard.objects.create(user=user, employee_id='AB001', designation='Dean')
```

## Usage Guide

### For Academic Board Members

1. **Login**: Select "Academic Board" role and log in
2. **Create Courses**:
   - Go to Dashboard
   - Click "Create New Course"
   - Fill in course details (code, name, description, credits)
   - Set "Lock Course" if you want to prevent teachers from editing

3. **Set Program Outcomes**:
   - Open a course
   - Click "Add" under Program Outcomes
   - Enter PO code (e.g., PO1) and description

4. **Assign Teachers**:
   - Open a course
   - Click "Assign" under Assigned Teachers
   - Select a teacher from the list

5. **Lock/Unlock Courses**:
   - Edit a course
   - Toggle "Lock Course" checkbox
   - Locked courses prevent teachers from adding learning outcomes or grades

### For Teachers

1. **Login**: Select "Teacher" role and log in
2. **View Courses**: See all courses assigned to you
3. **Add Learning Outcomes**:
   - Open a course (must not be locked)
   - Click "Add" under Learning Outcomes
   - Enter LO code (e.g., LO1) and description

4. **Upload Grades**:
   - Open a course (must not be locked)
   - Click "Upload Excel"
   - Prepare an Excel file with columns:
     - Student ID
     - Grade (A+, A, A-, B+, B, B-, C+, C, C-, D, F)
     - Percentage (optional)
   - Upload the file and optionally add semester/academic year

5. **Export Grades to PDF**:
   - Open a course
   - Click "Export PDF" to generate a PDF report of all grades

### For Students

1. **Login**: Select "Student" role and log in
2. **View Dashboard**: See enrolled courses and available grades
3. **View Course Details**:
   - Click "View Details" on any course
   - See your grade, program outcomes, and learning outcomes

## Excel File Format for Grade Upload

Your Excel file should have the following structure:

| Student ID | Grade | Percentage |
|------------|-------|------------|
| STU001     | A+    | 95.5       |
| STU002     | A     | 90.0       |
| STU003     | B+    | 85.5       |

**Notes**:
- Column names are case-insensitive
- "Student ID" column is required
- "Grade" column is required (valid values: A+, A, A-, B+, B, B-, C+, C, C-, D, F)
- "Percentage" column is optional
- The system will match Student IDs to existing Student profiles

## Project Structure

```
Eduu_Pace/
├── Eduu_Pace/          # Main project settings
│   ├── settings.py     # Django settings
│   ├── urls.py        # Main URL configuration
│   └── ...
├── edupace_app/       # Main application
│   ├── models.py      # Database models
│   ├── views.py       # View functions
│   ├── forms.py       # Form definitions
│   ├── utils.py       # Utility functions
│   ├── admin.py       # Admin configuration
│   ├── urls.py        # App URL configuration
│   └── templates/     # HTML templates
│       └── edupace_app/
│           ├── base.html
│           ├── login.html
│           ├── student/
│           ├── teacher/
│           └── academic_board/
├── media/             # User-uploaded files
├── staticfiles/       # Collected static files
└── manage.py
```

## Models Overview

- **Course**: Represents a course with code, name, description, credits, and lock status
- **Teacher**: Extends User, linked to courses they teach
- **Student**: Extends User, enrolled in courses
- **AcademicBoard**: Extends User, manages courses
- **ProgramOutcome**: Program outcomes for courses (created by Academic Board)
- **LearningOutcome**: Learning outcomes for courses (created by Teachers)
- **Grade**: Student grades for courses (uploaded by Teachers)

## Security & Permissions

- Role-based access control ensures users can only access features for their role
- Course locking prevents teachers from modifying locked courses
- Permission checks are implemented at both view and template levels
- All views require authentication and role verification

## Future Enhancements

The system is designed to be modular and scalable. Potential additions:
- Neo4j graph visualizations for course relationships
- Advanced analytics and reporting
- Email notifications
- Bulk student enrollment
- Grade statistics and charts
- Course prerequisites tracking

## Troubleshooting

### Common Issues

1. **"You do not have permission" errors**:
   - Ensure your user has the correct profile (Student/Teacher/AcademicBoard)
   - Check that you're logged in with the correct role

2. **Excel upload fails**:
   - Verify Excel file format matches the required structure
   - Check that Student IDs exist in the system
   - Ensure grade values are valid (A+, A, A-, etc.)

3. **PDF generation fails**:
   - Ensure pandas and reportlab are installed
   - Check that there are grades to export

## Development

### Running Tests
```bash
python manage.py test edupace_app
```

### Creating Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files
```bash
python manage.py collectstatic
```

## License

This project is for educational purposes.

## Support

For issues or questions, please check the code comments or Django documentation.

