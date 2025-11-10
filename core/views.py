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
                <title>Site under maintenance</title>
            </head>
            <body style="font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial; margin:40px;">
                <h1>Site under maintenance</h1>
                <p>We're performing security checks and maintenance. The site will be back soon.</p>
            </body>
        </html>
        """
        return HttpResponse(html, content_type='text/html')
