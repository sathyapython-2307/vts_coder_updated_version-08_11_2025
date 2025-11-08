from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Project, StudentProfile, StudentFollow, Notification
from django.utils import timezone
import json
from django.http import JsonResponse

@login_required
def student_project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    is_following = False
    if request.user.is_authenticated:
        is_following = StudentFollow.objects.filter(
            follower=request.user,
            following=project.student
        ).exists()
    return render(request, 'accounts/student_project_details.html', {
        'project': project,
        'is_following': is_following
    })

@login_required
def toggle_follow(request, student_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'})
    
    student = get_object_or_404(StudentProfile, id=student_id)
    
    # Don't allow self-following
    if student.user == request.user:
        return JsonResponse({'success': False, 'message': 'Cannot follow yourself'})
    
    follow, created = StudentFollow.objects.get_or_create(
        follower=request.user,
        following=student,
        defaults={'created_at': timezone.now()}
    )
    
    if not created:
        # User already follows, so unfollow
        follow.delete()
        following = False
    else:
        following = True
        # Create notification for new follower
        Notification.objects.create(
            recipient=student,
            sender=request.user,
            notification_type='follow'
        )
    
    return JsonResponse({
        'success': True,
        'following': following
    })

@login_required
def notifications(request):
    error_message = None
    try:
        # Get the student profile - explicitly handle the case where it doesn't exist
        try:
            student_profile = request.user.student_profile
        except AttributeError:
            return render(request, 'accounts/notifications.html', {
                'notifications': [],
                'error_message': "You don't have a student profile."
            })

        # Try to get notifications and related objects
        notifications = Notification.objects.filter(
            recipient=student_profile
        ).select_related('sender', 'project', 'hiring_process').order_by('-created_at')

        # Pre-process notification data safely
        for notification in notifications:
            if notification.data:
                try:
                    # Try to parse and validate JSON data
                    json_data = json.loads(notification.data)
                    if isinstance(json_data, dict):
                        # Format message for display
                        if 'job_title' in json_data:
                            notification.data = f"Job Title: {json_data.get('job_title')}"
                            if 'message' in json_data:
                                notification.data += f"\nMessage: {json_data.get('message')}"
                    else:
                        notification.data = str(notification.data)
                except (json.JSONDecodeError, TypeError, ValueError):
                    # If JSON is invalid, display as is
                    pass

        # Mark notifications as read
        notifications.filter(is_read=False).update(is_read=True)

    except AttributeError as e:
        # Handle case where user doesn't have a student profile
        notifications = Notification.objects.none()
        error_message = "You don't have a student profile."
    except Exception as e:
        # Handle other errors
        import traceback
        print('Error in notifications view:', str(e))
        traceback.print_exc()
        notifications = Notification.objects.none()
        error_message = str(e)

    return render(request, 'accounts/notifications.html', {
        'notifications': notifications,
        'error_message': error_message
    })


@login_required
def notifications_unread_json(request):
    """Return unread notifications (count + list) as JSON for polling clients."""
    try:
        student = request.user.student_profile
    except Exception:
        return JsonResponse({'success': False, 'error': 'No student profile'}, status=400)

    unread_qs = Notification.objects.filter(recipient=student, is_read=False).select_related('sender', 'project', 'hiring_process')

    notifs = []
    for n in unread_qs.order_by('-created_at')[:10]:
        item = {
            'id': n.id,
            'type': n.notification_type,
            'sender': n.sender.username,
            'created_at': n.created_at.isoformat(),
            'is_read': n.is_read,
        }
        if n.project:
            item['project'] = {'id': n.project.id, 'title': n.project.title}
        if n.hiring_process:
            item['hiring'] = {
                'id': n.hiring_process.id,
                'job_title': n.hiring_process.job_title,
                'message': n.hiring_process.message
            }
        # if data stored, try to include
        if n.data:
            try:
                item['data'] = json.loads(n.data)
            except Exception:
                item['data'] = n.data
        notifs.append(item)

    return JsonResponse({
        'success': True,
        'unread_count': unread_qs.count(),
        'notifications': notifs
    })

@login_required
@require_POST
def send_hire_notification(request, project_id):
    """Send a hire notification to the project owner"""
    project = get_object_or_404(Project, id=project_id)
    
    # Don't allow self-hiring
    if project.student.user == request.user:
        return JsonResponse({'success': False, 'message': 'Cannot hire yourself'})
    
    # Create hire notification
    Notification.objects.create(
        recipient=project.student,
        sender=request.user,
        notification_type='hire',
        project=project
    )
    
    return JsonResponse({
        'success': True,
        'message': f'Hire request sent to {project.student.student_name}'
    })