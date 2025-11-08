Render deployment checklist

This project uses Django + Whitenoise and is intended to be deployed to Render.
Follow these steps to deploy and avoid common issues (static, media, TLS):

1) Push to GitHub
   - Commit and push your code to the repository linked to Render.

2) Render service configuration (render.yaml is present)
   - Render will run the build/start commands in `render.yaml`. The current buildCommand:
     pip install -r requirements.txt; python manage.py migrate --noinput; python manage.py collectstatic --noinput
   - Start command: gunicorn core.wsgi:application --bind 0.0.0.0:8000

3) Environment variables (in Render dashboard -> Environment)
   - DJANGO_SECRET_KEY: set a secure random string
   - DATABASE_URL: Render can create a managed database; set the provided DATABASE_URL
   - DEBUG: set to `False` for production
   - (optional production flags): SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE (set to "True"), SECURE_HSTS_SECONDS (e.g. 31536000)
   - CSRF_TRUSTED_ORIGINS: comma-separated origins (e.g. https://your-site.onrender.com)

4) Static & media files
   - Static files are collected to `/staticfiles` by collectstatic and served by Render (render.yaml maps `/static` to `staticfiles`).
   - Media files in the `media/` directory that are part of the repository will be served from `/media` via Render staticDirs.
   - IMPORTANT: User-uploaded media should be stored in object storage (S3 or similar). Render's staticDirs do not persist runtime uploads across deploys.
     - Use `django-storages` + S3 or another external storage if your app needs uploads to persist.

5) TLS / "Dangerous site" troubleshooting
   - For Render-provided `*.onrender.com` domains, TLS is provisioned automatically; ensure your service's domain shows a valid HTTPS certificate in Render dashboard.
   - For custom domains, ensure DNS is pointed to Render and Render's TLS certificate provisioning completes.
   - If the browser shows a "Dangerous site" page:
     - Check the domain certificate in the browser.
     - Check for any redirects to non-HTTPS links.
     - Confirm the Render domain is correct and certificate status is "issued" in Render dashboard.

6) Post-deploy verification
   - Open the site in a private browser window.
   - Check these endpoints:
     - /health/ should return OK
     - /static/css/... main CSS should return HTTP 200
     - /media/... images should return 200 (if present in repo)
   - Use the browser network tab for debug.

7) If CSS or images 404
   - Confirm collectstatic ran during build and the file names were included in the collectstatic output.
   - If missing user-uploaded files, configure external storage.

8) Pin dependencies
   - `requirements.txt` now contains pinned versions to avoid unexpected upstream changes. If you need to upgrade, test locally and update the pins.

If you want, I can also:
- Add `django-storages` + S3 configuration and a small deployment guide for persistent media.
- Monitor your Render build logs if you provide the Render service link or share the build log output.

*** End of file"