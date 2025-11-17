from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from edupace_app.models import Student, Teacher, AcademicBoard


class Command(BaseCommand):
    help = 'Creates sample users for testing (Student, Teacher, and Academic Board)'

    def handle(self, *args, **options):
        # Create Academic Board user
        if not User.objects.filter(username='board1').exists():
            board_user = User.objects.create_user(
                username='board1',
                password='board123',
                first_name='Academic',
                last_name='Board',
                email='board@edupace.com'
            )
            AcademicBoard.objects.create(
                user=board_user,
                employee_id='AB001',
                designation='Dean'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Academic Board user: board1 / board123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Academic Board user already exists')
            )

        # Create Teacher user
        if not User.objects.filter(username='teacher1').exists():
            teacher_user = User.objects.create_user(
                username='teacher1',
                password='teacher123',
                first_name='Jane',
                last_name='Smith',
                email='teacher@edupace.com'
            )
            Teacher.objects.create(
                user=teacher_user,
                employee_id='TCH001',
                department='Computer Science'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Teacher user: teacher1 / teacher123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Teacher user already exists')
            )

        # Create Student user
        if not User.objects.filter(username='student1').exists():
            student_user = User.objects.create_user(
                username='student1',
                password='student123',
                first_name='John',
                last_name='Doe',
                email='student@edupace.com'
            )
            Student.objects.create(
                user=student_user,
                student_id='STU001',
                enrollment_date='2024-01-01',
                program='Computer Science'
            )
            self.stdout.write(
                self.style.SUCCESS(f'✓ Created Student user: student1 / student123')
            )
        else:
            self.stdout.write(
                self.style.WARNING('Student user already exists')
            )

        self.stdout.write(
            self.style.SUCCESS('\n' + '='*60)
        )
        self.stdout.write(
            self.style.SUCCESS('Sample users created successfully!')
        )
        self.stdout.write(
            self.style.SUCCESS('='*60)
        )
        self.stdout.write('\nLogin credentials:')
        self.stdout.write('  Academic Board: username=board1, password=board123')
        self.stdout.write('  Teacher:        username=teacher1, password=teacher123')
        self.stdout.write('  Student:        username=student1, password=student123')
        self.stdout.write('\n')

