from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import Project, ProjectView, ProjectLike, StudentProfile

def check_student_profile(view_func):
    def _wrapped_view(request, *args, **kwargs):
        try:
            # Try to access the student profile
            student_profile = request.user.student_profile
            return view_func(request, *args, **kwargs)
        except ObjectDoesNotExist:
            # Redirect to an error page or admin home if user has no profile
            if request.user.is_superuser:
                return redirect('admin_home')
            # You might want to create a dedicated error template for this
            return render(request, 'accounts/no_profile.html', {
                'message': 'No student profile found. Please contact an administrator.'
            })
    return _wrapped_view

@login_required
def student_projects(request):
    projects = Project.objects.filter(student=request.user.student_profile).order_by('-created_at')
    # Build list of project IDs for which to record views (not admin, not owner)
    record_view_ids = []
    if not request.user.is_superuser:
        for project in projects:
            if request.user != project.student.user:
                record_view_ids.append(project.id)
    return render(request, 'accounts/projects.html', {
        'projects': projects,
        'record_view_ids': record_view_ids
    })

@login_required
def delete_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, student=request.user.student_profile)
    if request.method == 'POST':
        project.delete()
        return JsonResponse({'success': True, 'message': 'Project deleted successfully'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, student=request.user.student_profile)
    
    if request.method == 'POST':
        # Update project fields
        project.title = request.POST.get('title', project.title)
        project.description = request.POST.get('description', project.description)
        project.category = request.POST.get('category', project.category)
        project.tags = request.POST.get('tags', project.tags)
        project.visibility = request.POST.get('visibility', project.visibility)
        project.allow_downloads = request.POST.get('allow_downloads') == 'on'
        project.output_link = request.POST.get('output_link', project.output_link)
        project.project_link = request.POST.get('project_link', project.project_link)
        
        # Handle screenshot if provided
        if 'screenshot' in request.FILES:
            project.screenshot = request.FILES['screenshot']
        
        project.save()
        return JsonResponse({'success': True, 'message': 'Project updated successfully'})
    
    # Return project data for editing
    return JsonResponse({
        'success': True,
        'project': {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'category': project.category,
            'tags': project.tags,
            'visibility': project.visibility,
            'allow_downloads': project.allow_downloads,
            'output_link': project.output_link,
            'project_link': project.project_link,
            'screenshot_url': project.screenshot.url if project.screenshot else None
        }
    })

@login_required
def remove_from_recent_uploads(request, project_id):
    """Remove project from Recent Uploads section only (doesn't delete the project)"""
    if request.method == 'POST':
        # This is just for UI removal - the project remains in the database
        return JsonResponse({'success': True, 'message': 'Removed from Recent Uploads'})
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def toggle_project_like(request, project_id):
    if request.method == 'POST':
        project = get_object_or_404(Project, id=project_id)
        like, created = ProjectLike.objects.get_or_create(
            project=project,
            user=request.user,
            defaults={'created_at': timezone.now()}
        )
        
        if not created:
            # User already liked the project, so unlike it
            like.delete()
            liked = False
        else:
            liked = True
            
        return JsonResponse({
            'success': True,
            'liked': liked,
            'likeCount': project.like_count()
        })
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
@check_student_profile
def student_home(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            # Handle AJAX project creation
            project = Project.objects.create(
                student=request.user.student_profile,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                category=request.POST.get('category'),
                tags=request.POST.get('tags'),
                visibility=request.POST.get('visibility'),
                allow_downloads=request.POST.get('allow_downloads') == 'on',
                output_link=request.POST.get('output_link', ''),
                project_link=request.POST.get('project_link', '')
            )
            
            # Handle screenshot if provided
            if 'screenshot' in request.FILES:
                project.screenshot = request.FILES['screenshot']
                project.save()
            
            return JsonResponse({'success': True, 'message': 'Project created successfully'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    # Pass user_projects for Recent Uploads with additional data
    user_projects = Project.objects.filter(student=request.user.student_profile).order_by('-created_at')[:6]
    
    # Add URLs and additional data to each project
    for project in user_projects:
        project.edit_url = f'/accounts/project/{project.id}/edit/'
        project.delete_url = f'/accounts/project/{project.id}/remove-from-recent/'
        project.time_ago = project.created_at.strftime('%b %d, %Y')
        project.status = 'Published'  # All projects in Recent Uploads are considered published
    
    return render(request, 'accounts/student_home.html', {'user_projects': user_projects})

def view_project(request, project_id):
    project = Project.objects.get(id=project_id)
    user = request.user
    # Only count if not admin and not the owner
    if not user.is_superuser and user != project.student.user:
        ProjectView.objects.get_or_create(project=project, user=user)
    return render(request, 'accounts/project_detail.html', {'project': project})


@login_required
def record_project_view(request):
    print("\n=== Project View Request ===")
    print(f"Method: {request.method}")
    print(f"User: {request.user.username} (authenticated: {request.user.is_authenticated})")
    print(f"POST data: {request.POST}")
    print("Headers:")
    for key, value in request.headers.items():
        print(f"  {key}: {value}")
    
    if request.method == 'POST' and request.user.is_authenticated:
        project_id = request.POST.get('project_id')
        print(f"\nProcessing project_id: {project_id}")
        
        try:
            project = Project.objects.get(id=project_id)
            print(f"Found project: {project.title}")
            
            user = request.user
            print(f"User is superuser: {user.is_superuser}")
            print(f"Project owner: {project.student.user.username}")
            
            # Only create new view if not admin and not the owner
            if not user.is_superuser and user != project.student.user:
                view, created = ProjectView.objects.get_or_create(project=project, user=user)
                print(f"View record {'created' if created else 'already exists'}")
                if created:
                    print("New view recorded!")
                else:
                    print("User has already viewed this project")
            else:
                print("View not counted - user is admin or project owner")
            
            # Always return current count
            current_count = project.view_count()
            print(f"Current view count: {current_count}")
            
            response_data = {
                'success': True,
                'newCount': current_count,
                'projectId': project_id
            }
            print(f"Sending response: {response_data}")
            return JsonResponse(response_data)
            
        except Project.DoesNotExist:
            print(f"Error: Project {project_id} not found")
            return JsonResponse({'success': False, 'error': 'Project not found.'})
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
            return JsonResponse({'success': False, 'error': str(e)})
    
    print("Invalid request - not POST or user not authenticated")
    return JsonResponse({'success': False, 'error': 'Invalid request.'})
