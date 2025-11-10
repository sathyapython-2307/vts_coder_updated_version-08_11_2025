from django.http import HttpResponse


def health(request):
    """Simple health check endpoint used by monitoring or deployment checks."""
    return HttpResponse('OK', content_type='text/plain')


def maintenance(request):
    """Simple maintenance page returned while we clean up site/security issues.

    This page is intentionally minimal and safe so Google/visitors see no
    suspicious content while we investigate further.
    """
    html = """
<!doctype html>
<html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <!-- Google Search Console verification (keeps verification in place while maintenance page is shown) -->
        <meta name="google-site-verification" content="A-K3ZNVPtR7ltMB6VXoewuE_q3dWnTZ5j1QcyZVqZdQ" />
        <title>Site under maintenance</title>
    </head>
    <body style="font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:40px;">
        <h1>Site under maintenance</h1>
        <p>We're performing security checks and maintenance. The site will be back soon.</p>
    </body>
</html>
"""

    # Return 503 Service Unavailable while maintenance/security checks are
    # performed. This signals crawlers and automated scanners that the
    # outage is temporary. We include a Retry-After header (seconds).
    response = HttpResponse(html, content_type='text/html', status=503)
    response['Retry-After'] = '3600'  # advise clients to retry after 1 hour
    return response
