from django.core.management.base import BaseCommand
from accounts.models import Project
import re


class Command(BaseCommand):
    help = 'Scan Project records for suspicious keywords or downloadable links'

    SUSPICIOUS_PATTERNS = [
        r"\.exe",
        r"\.apk",
        r"\.zip",
        r"\.rar",
        r"free money",
        r"bank",
        r"credit card",
        r"paypal",
        r"verify",
        r"confirm",
        r"download",
        r"\.scr",
        r"\.bat",
    ]

    combined_re = re.compile("(?:" + ")|(?:".join(SUSPICIOUS_PATTERNS) + ")", re.IGNORECASE)

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=0, help='Limit number of projects to scan (0 = all)')

    def handle(self, *args, **options):
        limit = options.get('limit', 0) or None
        qs = Project.objects.all().order_by('id')
        if limit:
            qs = qs[:limit]

        total = qs.count() if hasattr(qs, 'count') else len(qs)
        self.stdout.write(f'Scanning {total} projects for suspicious content...')

        findings = []

        for proj in qs:
            text = ' '.join(filter(None, [
                getattr(proj, 'title', '') or '',
                getattr(proj, 'description', '') or '',
                getattr(proj, 'tags', '') or '',
                getattr(proj, 'project_link', '') or '',
                getattr(proj, 'output_link', '') or '',
            ]))

            matches = self.combined_re.findall(text)
            if matches:
                findings.append((proj.id, proj.student.student_name if proj.student else 'N/A', proj.title, list(set([m.lower() for m in matches]))))

        if not findings:
            self.stdout.write(self.style.SUCCESS('No suspicious content found in projects.'))
            return

        self.stdout.write(self.style.WARNING(f'Found {len(findings)} projects with suspicious matches:'))
        for pid, student_name, title, matches in findings:
            self.stdout.write(f'- Project ID {pid} | Student: {student_name} | Title: {title} | Matches: {matches}')

        self.stdout.write('Scan complete.')
