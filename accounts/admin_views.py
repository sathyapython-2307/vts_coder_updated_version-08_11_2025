from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from accounts.models import StudentProfile, Project
from django.utils.timesince import timesince

def admin_required(view_func):
    decorated_view_func = user_passes_test(lambda u: u.is_superuser)(view_func)
    return decorated_view_func

@admin_required
def admin_home(request):
    candidates = StudentProfile.objects.count()
    total_projects = Project.objects.count()
    return render(request, 'accounts/admin_home.html', {
        'candidates': candidates,
        'total_projects': total_projects,
    })

@admin_required
def admin_projects(request):
    # Get all projects ordered by most recent first
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'accounts/admin_projects.html', {
        'projects': projects
    })

@admin_required
def admin_profiles(request):
    try:
        students = StudentProfile.objects.all()
        
        # Search functionality
        search_query = request.GET.get('search', '').strip()
        if search_query:
            students = students.filter(student_name__icontains=search_query)
        
        # Month filter
        month = request.GET.get('month', '').strip()
        selected_month = month  # Store original value for template
        if month and month.isdigit():
            month_int = int(month)
            if 1 <= month_int <= 12:  # Validate month range
                students = students.filter(course_joined_date__month=month_int)
        
        # Year filter
        year = request.GET.get('year', '').strip()
        selected_year = year  # Store original value for template
        if year and year.isdigit():
            students = students.filter(course_joined_date__year=int(year))
        
        # Course filter
        course = request.GET.get('course', '').strip()
        if course:
            students = students.filter(course_details__icontains=course)
        
        # Get unique years and courses for filter options
        unique_years = StudentProfile.objects.dates('course_joined_date', 'year', order='DESC')
        unique_courses = StudentProfile.objects.exclude(course_details='').values_list('course_details', flat=True).distinct().order_by('course_details')
        
        # Order the results
        students = students.order_by('student_name')

        # Calculate derived properties for each student to use in template
        for student in students:
            # number of projects
            student.projects_count = student.projects.count()
            # total views across all projects
            student.projects_views = sum(p.views.count() for p in student.projects.all())
        
        context = {
            'students': students,
            'unique_years': unique_years,
            'unique_courses': unique_courses,
            'months': [
                (1, 'January'), (2, 'February'), (3, 'March'), (4, 'April'),
                (5, 'May'), (6, 'June'), (7, 'July'), (8, 'August'),
                (9, 'September'), (10, 'October'), (11, 'November'), (12, 'December')
            ],
            'selected_month': selected_month,
            'selected_year': selected_year,
            'selected_course': course,
            'search_query': search_query,
        }
        
        return render(request, 'accounts/admin_profiles.html', context)
        
    except Exception as e:
        print(f"Error in admin_profiles view: {str(e)}")  # For debugging
        return render(request, 'accounts/admin_profiles.html', {
            'students': StudentProfile.objects.all().order_by('student_name'),
            'error_message': 'An error occurred while filtering the results.'
        })
    
    return render(request, 'accounts/admin_profiles.html', context)

@admin_required
def student_projects_api(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    projects = student.projects.all().order_by('-created_at')
    
    projects_data = [{
        'id': project.id,
        'title': project.title,
        'description': project.description,
        'project_link': project.project_link,
        'output_link': project.output_link,
        'screenshot': project.screenshot.url if project.screenshot else None,
        'created_at_display': timesince(project.created_at)
    } for project in projects]
    
    return JsonResponse({'projects': projects_data})

@admin_required
def student_project_details(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    # For admin, show all projects (both public and private)
    projects = student.projects.all().order_by('-created_at')
    return render(request, 'accounts/student_project_details.html', {
        'student': student,
        'projects': projects,
        'is_admin': True
    })

def public_student_projects(request):
    students = StudentProfile.objects.all().order_by('student_name')
    for student in students:
        student.public_projects = student.projects.filter(visibility='Public').order_by('-created_at')
    return render(request, 'accounts/public_student_projects.html', {
        'students': students
    })
