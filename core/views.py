from django.http import HttpResponse


def health(request):
    """Simple health check endpoint used by monitoring or deployment checks."""
    return HttpResponse('OK', content_type='text/plain')
