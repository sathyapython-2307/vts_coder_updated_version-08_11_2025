from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.conf import settings
import razorpay
import json

from .models import RecruiterProfile
from django.db.models import Count, Q, Sum
from .models import StudentProfile, Project, HiringProcess, Notification

@login_required
def student_projects(request):
    """View all student projects"""
    try:
        if not hasattr(request.user, 'recruiter_profile'):
            return HttpResponseForbidden("Access Denied - No recruiter profile found")

        recruiter = request.user.recruiter_profile
        if recruiter.status != 'approved':
            return HttpResponseForbidden("Your account is pending approval")

        # Get all public projects with their students
        projects = Project.objects.filter(
            visibility='Public'
        ).select_related('student').order_by('-created_at')

        # Get unique tags from all projects
        all_tags = set()
        projects_with_tags = []
        for project in projects:
            tags = [tag.strip() for tag in project.tags.split(',')] if project.tags else []
            all_tags.update(tags)
            projects_with_tags.append({
                'project': project,
                'tags': tags
            })

        # Sort tags alphabetically
        sorted_tags = sorted(list(all_tags))

        return render(request, 'accounts/recruiter_student_projects.html', {
            'projects': projects_with_tags,
            'all_tags': sorted_tags,
            'recruiter': recruiter,
            'company_name': recruiter.company_name,
            'contact_person': recruiter.contact_person,
            'active_tab': 'projects'
        })
    except Exception as e:
        print(f"Error in student_projects: {str(e)}")
        return HttpResponseForbidden(str(e))

@login_required
def browse_talent(request):
    """Browse student talent profiles"""
    print(f"\n=== Browse Talent View ===")
    print(f"User: {request.user.username}")
    print(f"Is authenticated: {request.user.is_authenticated}")
    try:
        # Ensure user has recruiter profile and is approved
        if not hasattr(request.user, 'recruiter_profile'):
            print(f"User {request.user.username} has no recruiter profile")
            return HttpResponseForbidden("Access Denied - No recruiter profile found")

        recruiter = request.user.recruiter_profile
        print(f"Recruiter status: {recruiter.status}")
        if recruiter.status != 'approved':
            return HttpResponseForbidden("Your account is pending approval")
            
        # Get all students with their related data
        students = StudentProfile.objects.all().prefetch_related(
            'projects', 
            'followers'
        ).order_by('-profile_views')
        
        # Get unique courses for filter
        courses = StudentProfile.objects.values_list(
            'course_details', 
            flat=True
        ).distinct().order_by('course_details')
        
        return render(request, 'accounts/browse_talent.html', {
            'students': students,
            'courses': courses,
            'recruiter': recruiter,
            'company_name': recruiter.company_name,
            'contact_person': recruiter.contact_person,
        })
        
    except Exception as e:
        return HttpResponseForbidden(str(e))

@login_required
def toggle_save_student(request, student_id):
    """Toggle save/unsave a student profile"""
    print(f"\n=== Toggle Save Student ===")
    print(f"Method: {request.method}")
    print(f"Student ID: {student_id}")
    print(f"User: {request.user.username}")
    print(f"Headers: {dict(request.headers)}")
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
        
    try:
        student = get_object_or_404(StudentProfile, id=student_id)
        print(f"Found student: {student.student_name}")
        
        recruiter = request.user.recruiter_profile
        print(f"Recruiter: {recruiter.company_name}")
        
        if student in recruiter.saved_students.all():
            print("Removing student from saved list")
            recruiter.saved_students.remove(student)
            saved = False
        else:
            print("Adding student to saved list")
            recruiter.saved_students.add(student)
            saved = True
        
        saved_count = recruiter.saved_students.count()
        print(f"New saved count: {saved_count}")
        
        return JsonResponse({
            'success': True,
            'saved': saved,
            'savedCount': saved_count
        })
    except Exception as e:
        print(f"Error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def initiate_hiring_process(request, student_id):
    """Initiate a hiring process for a student"""
    if request.method == 'POST':
        try:
            student = get_object_or_404(StudentProfile, id=student_id)
            recruiter = request.user.recruiter_profile
            
            # Create hiring process
            hiring_process = HiringProcess.objects.create(
                recruiter=recruiter,
                student=student,
                job_title=request.POST.get('job_title'),
                message=request.POST.get('message')
            )
            
            # Increment hiring process count
            recruiter.hiring_process_count += 1
            recruiter.save()
            
            # Create notification for student and attach hiring_process + data
            Notification.objects.create(
                recipient=student,
                sender=request.user,
                notification_type='hire',
                project=None,  # No specific project for general hiring
                hiring_process=hiring_process,
                data=json.dumps({
                    'job_title': hiring_process.job_title,
                    'message': hiring_process.message
                })
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Hiring process initiated successfully',
                'hiring_count': recruiter.hiring_process_count
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
def view_student_profile(request, student_id):
    """View a student's profile"""
    try:
        student = get_object_or_404(StudentProfile, id=student_id)
        projects = student.projects.filter(visibility='Public').order_by('-created_at')
        
        # Increment profile views
        student.increment_profile_views()
        
        # Check if student is saved by the recruiter
        is_saved = request.user.recruiter_profile.saved_students.filter(id=student_id).exists()
        
        recruiter = request.user.recruiter_profile
        return render(request, 'accounts/student_profile_recruiter_view.html', {
            'student': student,
            'projects': projects,
            'is_saved': is_saved,
            'recruiter': recruiter,
            'company_name': recruiter.company_name,
            'contact_person': recruiter.contact_person
        })
    except Exception as e:
        return HttpResponseForbidden(str(e))

@login_required
def view_project_details(request, project_id):
    """View project details"""
    try:
        project = get_object_or_404(Project, id=project_id)
        
        # Only allow viewing public projects
        if project.visibility != 'Public':
            return HttpResponseForbidden("This project is private")
            
        # Increment project views - using get_or_create to avoid duplicates
        project.views.get_or_create(user=request.user)
        
        recruiter = request.user.recruiter_profile
        return render(request, 'accounts/project_details_recruiter_view.html', {
            'project': project,
            'tags': project.tags.split(',') if project.tags else [],
            'recruiter': recruiter,
            'company_name': recruiter.company_name,
            'contact_person': recruiter.contact_person
        })
    except Exception as e:
        return HttpResponseForbidden(str(e))

@login_required
def recruiter_home(request):
    print(f"User attempting to access recruiter home: {request.user.username}")
    print(f"Is superuser: {request.user.is_superuser}")
    print(f"Is staff: {request.user.is_staff}")
    
    try:
        # Check if user has a recruiter profile
        if not hasattr(request.user, 'recruiter_profile'):
            print(f"User {request.user.username} does not have a recruiter profile")
            return HttpResponseForbidden("Access Denied - No recruiter profile found")

        recruiter = request.user.recruiter_profile
        print(f"Recruiter status: {recruiter.status}")
        
        if recruiter.status != 'approved':
            print(f"Recruiter {request.user.username} is not approved")
            return HttpResponseForbidden("Your account is pending approval")
        
        # Get top students (based on project count and views)
        top_students = StudentProfile.objects.annotate(
            project_count=Count('projects'),
            total_views=Count('projects__views')
        ).order_by('-project_count', '-total_views')[:6]

        # Get recent public projects
        recent_projects = Project.objects.filter(
            visibility='Public'
        ).select_related('student').order_by('-created_at')[:6]

        # Prepare projects with split tags
        projects_with_tags = []
        for project in recent_projects:
            tags = project.tags.split(',') if project.tags else []
            projects_with_tags.append({
                'project': project,
                'tags': tags
            })

        # Calculate total profile views from all viewed student profiles
        total_profile_views = StudentProfile.objects.filter(
            id__in=recruiter.saved_students.values_list('id', flat=True)
        ).aggregate(total_views=Sum('profile_views'))['total_views'] or 0
        
        context = {
            'recruiter': recruiter,
            'company_name': recruiter.company_name,
            'contact_person': recruiter.contact_person,
            'top_students': top_students,
            'recent_projects': projects_with_tags,
            'profile_views': total_profile_views,
            'saved_profiles': recruiter.saved_students.count(),
            'messages_sent': recruiter.messages_count,
            'hiring_process': recruiter.hiring_process_count
        }
        return render(request, 'accounts/recruiter_home.html', context)
    except Exception as e:
        print(f"Error in recruiter_home: {str(e)}")
        import traceback
        print(traceback.format_exc())  # Print full traceback
        return HttpResponseForbidden(f"Access Denied - Error: {str(e)}")

# Initialize Razorpay client
client = razorpay.Client(auth=("rzp_test_RbaHeEXOm8aOxe", "qsQeLpxFeH0ZLx68BkD3771h"))

def recruiter_register_view(request):
    return render(request, 'accounts/recruiter_register.html')

@csrf_exempt
def create_recruiter_order(request):
    if request.method == "POST":
        try:
            # Handle form data instead of JSON
            email = request.POST.get('email')
            if not email:
                return JsonResponse({'error': 'Email is required'}, status=400)

            amount = 99900  # Amount in paise (₹999.00)
            
            # Create Razorpay Order
            order_data = {
                'amount': amount,
                'currency': 'INR',
                'receipt': f"order_rcpt_{email}"
            }
            
            order = client.order.create(data=order_data)
            
            return JsonResponse({
                'order_id': order['id'],
                'amount': amount
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@csrf_exempt
@login_required
def saved_profiles(request):
    """View saved student profiles"""
    try:
        recruiter = request.user.recruiter_profile
        saved_students = recruiter.saved_students.all().prefetch_related('projects')
        
        # For each student, get their public projects
        students_with_projects = []
        for student in saved_students:
            public_projects = student.projects.filter(visibility='Public').order_by('-created_at')[:3]
            students_with_projects.append({
                'student': student,
                'projects': public_projects,
                'skills': set().union(*[set(p.tags.split(',')) for p in public_projects if p.tags])
            })
        
        return render(request, 'accounts/saved_profiles.html', {
            'recruiter': recruiter,
            'company_name': recruiter.company_name,
            'contact_person': recruiter.contact_person,
            'students_with_projects': students_with_projects
        })
    except Exception as e:
        return HttpResponseForbidden(str(e))

def complete_recruiter_registration(request):
    if request.method == "POST":
        try:
            # Create user - initially not staff until approved
            user = User.objects.create_user(
                username=request.POST['email'],
                email=request.POST['email'],
                password=request.POST['password'],
                is_staff=False,  # Will be set to True when approved
                is_superuser=False
            )
            
            # Create recruiter profile
            recruiter = RecruiterProfile.objects.create(
                user=user,
                company_name=request.POST['company_name'],
                company_linkedin=request.POST.get('company_linkedin', ''),
                company_address=request.POST['company_address'],
                contact_person=request.POST['contact_person'],
                phone_number=request.POST['phone_number'],
                email=request.POST['email'],
                payment_status='completed',
                payment_id=request.POST['payment_id'],
                status='pending'  # Explicitly set initial status
            )
            
            # Handle company logo if provided
            if 'company_logo' in request.FILES:
                recruiter.company_logo = request.FILES['company_logo']
                recruiter.save()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            if 'user' in locals():
                user.delete()
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request'})