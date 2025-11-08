from .models import Notification

def notifications_processor(request):
    unread_count = 0
    if request.user.is_authenticated and not request.user.is_superuser:
        try:
            unread_count = Notification.objects.filter(
                recipient=request.user.student_profile,
                is_read=False
            ).count()
        except:
            pass
    return {'unread_notifications_count': unread_count}