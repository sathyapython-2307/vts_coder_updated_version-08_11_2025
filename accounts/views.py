from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

from .models import StudentProfile, Project, StudentFollow, Notification

import datetime

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('login')

@login_required
def student_profile_view(request, student_id):
    student = get_object_or_404(StudentProfile, id=student_id)
    projects = Project.objects.filter(student=student).order_by('-created_at')
    
    # Check if current user is following this student
    follow_status = 'none'
    if request.user != student.user:
        follow = StudentFollow.objects.filter(follower=request.user, following=student).first()
        if follow:
            follow_status = follow.status
    
    # Get counts (only count accepted followers)
    projects_count = projects.count()
    followers_count = StudentFollow.objects.filter(following=student, status='accepted').count()
    following_count = StudentFollow.objects.filter(follower=student.user, status='accepted').count()
    
    # Get pending follow requests if viewing own profile
    pending_requests = []
    if request.user == student.user:
        pending_requests = StudentFollow.objects.filter(following=student, status='pending')
    
    context = {
        'student': student,
        'projects': projects,
        'projects_count': projects_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'follow_status': follow_status,
        'pending_requests': pending_requests,
    }
    
    return render(request, 'accounts/student_profile.html', context)
    
@login_required
@require_POST
def request_follow(request, student_id):
    print(f"Received follow request for student {student_id} from {request.user.username}")
    
    target_student = get_object_or_404(StudentProfile, id=student_id)
    print(f"Target student found: {target_student.student_name}")
    
    if request.user == target_student.user:
        print("User attempting to follow themselves")
        return JsonResponse({'success': False, 'message': 'Cannot follow yourself'})
    
    # Check if a follow relationship already exists
    existing_follow = StudentFollow.objects.filter(
        follower=request.user,
        following=target_student
    ).first()
    
    if existing_follow:
        print(f"Existing follow found with status: {existing_follow.status}")
        return JsonResponse({
            'success': False,
            'status': existing_follow.status,
            'message': f'Already {existing_follow.status}'
        })
        
    # Create new follow request
    follow = StudentFollow.objects.create(
        follower=request.user,
        following=target_student,
        status='pending'
    )
    print(f"Created new follow request with status: {follow.status}")
    
    # Create notification
    Notification.objects.create(
        recipient=target_student,
        sender=request.user,
        notification_type='follow',
    )
    print("Created notification")
        
    return JsonResponse({
        'success': True,
        'status': 'pending',
        'message': 'Follow request sent'
    })
    
@login_required
@require_POST
def handle_follow_request(request, follow_id):
    print(f"Processing follow request {follow_id}")
    print(f"Request user: {request.user.username}")
    print(f"Action: {request.POST.get('action')}")
    
    follow_request = get_object_or_404(StudentFollow, id=follow_id)
    print(f"Follow request found - from {follow_request.follower.username} to {follow_request.following.student_name}")
    
    # Only allow the target user to accept/reject
    if request.user != follow_request.following.user:
        print(f"Unauthorized - request user {request.user.username} doesn't match target {follow_request.following.user.username}")
        return JsonResponse({'success': False, 'message': 'Unauthorized'})
    
    action = request.POST.get('action')
    if action == 'accept':
        print("Accepting follow request")
        follow_request.status = 'accepted'
        follow_request.save()
        
        # Create notification for accepted follow
        notification = Notification.objects.create(
            recipient=follow_request.follower.student_profile,
            sender=request.user,
            notification_type='follow_accepted',
        )
        print(f"Created notification: {notification}")
        message = 'Follow request accepted'
        
    elif action == 'reject':
        print("Rejecting follow request")
        follow_request.status = 'rejected'
        follow_request.save()
        message = 'Follow request rejected'
    else:
        print(f"Invalid action: {action}")
        return JsonResponse({'success': False, 'message': 'Invalid action'})
    
    # Get updated follower count
    followers_count = StudentFollow.objects.filter(
        following=follow_request.following,
        status='accepted'
    ).count()
    print(f"Updated follower count: {followers_count}")
        
    return JsonResponse({
        'success': True,
        'message': message,
        'followers_count': followers_count
    })
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from .models import StudentProfile
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage

@csrf_exempt
def add_student(request):
	if request.method == 'POST':
		username = request.POST.get('username')
		password = request.POST.get('password')
		student_name = request.POST.get('student_name')
		student_contact = request.POST.get('student_contact')
		student_email = request.POST.get('student_email')
		student_address = request.POST.get('student_address')
		course_joined_date = request.POST.get('course_joined_date')
		course_details = request.POST.get('course_details')
		student_image = request.FILES.get('student_image')
		if not username or not password:
			return JsonResponse({'success': False, 'error': 'Username and password required.'})
		if User.objects.filter(username=username).exists():
			return JsonResponse({'success': False, 'error': 'Username already exists.'})
		# Validate course_joined_date: must not be in the future
		try:
			joined_date = datetime.datetime.strptime(course_joined_date, '%Y-%m-%d').date()
			today = datetime.date.today()
			if joined_date > today:
				return JsonResponse({'success': False, 'error': 'Course joined date must not be in the future.'})
		except Exception:
			return JsonResponse({'success': False, 'error': 'Invalid course joined date.'})
		# Email and phone validation (format checks)
		from django.core.validators import EmailValidator
		from django.core.exceptions import ValidationError
		import re

		try:
			EmailValidator()(student_email)
		except ValidationError:
			return JsonResponse({'success': False, 'error': 'Please enter a valid email address.'})

		if not re.match(r"^\+?[1-9]\d{7,14}$", student_contact or ""):
			return JsonResponse({'success': False, 'error': 'Invalid contact number. Enter a valid international number (e.g., +14155552671).'})
		# Validate email uniqueness
		if StudentProfile.objects.filter(student_email=student_email).exists():
			return JsonResponse({'success': False, 'error': 'Email already exists.'})
		# Validate contact uniqueness
		if StudentProfile.objects.filter(student_contact=student_contact).exists():
			return JsonResponse({'success': False, 'error': 'Contact already exists.'})
		user = User.objects.create_user(username=username, password=password)
		user.is_superuser = False
		user.is_staff = False
		user.save()
		student_profile = StudentProfile(
			user=user,
			student_name=student_name,
			student_contact=student_contact,
			student_email=student_email,
			student_address=student_address,
			course_joined_date=course_joined_date,
			course_details=course_details
		)
		if student_image:
			student_profile.image = student_image
		student_profile.save()
		candidate_count = StudentProfile.objects.count()
		return JsonResponse({'success': True, 'candidates': candidate_count})
	return JsonResponse({'success': False, 'error': 'Invalid request.'})

def login_view(request):
	if request.method == 'POST':
		user_type = request.POST.get('user_type')
		email = request.POST.get('email')
		password = request.POST.get('password')
		user = authenticate(request, username=email, password=password)
		if user is not None:
			if user_type == 'admin' and user.is_superuser:
				login(request, user)
				return redirect('/admin-home/')
			elif user_type == 'student' and not user.is_superuser and not user.is_staff:
				login(request, user)
				return redirect('/student-home/')
			elif user_type == 'recruiter' and not user.is_superuser:
				try:
					recruiter = user.recruiter_profile
					if recruiter.status == 'approved':
						login(request, user)
						return redirect('/recruiter-home/')  # You'll need to create this URL and view
					else:
						messages.error(request, 'Your account is pending approval')
				except:
					messages.error(request, 'Invalid credentials for recruiter')
			else:
				messages.error(request, 'Invalid credentials for selected user type')
		else:
			messages.error(request, 'Invalid email or password')
	return render(request, 'accounts/login.html')
