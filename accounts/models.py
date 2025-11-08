from django.db import models
from django.contrib.auth.models import User
from django.utils.functional import cached_property


class RecruiterProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recruiter_profile')
    company_name = models.CharField(max_length=200)
    company_linkedin = models.URLField(blank=True, null=True)
    company_logo = models.ImageField(upload_to='company_logos/', blank=True, null=True)
    company_address = models.TextField()
    contact_person = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=30)
    email = models.EmailField()
    payment_status = models.CharField(max_length=20, default='pending')
    payment_id = models.CharField(max_length=100, blank=True, null=True)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, default=999.00)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved')
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Approval status of the recruiter'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    profile_views = models.IntegerField(default=0)
    saved_students = models.ManyToManyField('StudentProfile', related_name='saved_by_recruiters', blank=True)
    messages_count = models.IntegerField(default=0)
    hiring_process_count = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.company_name} - {self.contact_person}"
        
    def increment_hiring_process(self):
        self.hiring_process_count += 1
        self.save()
class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_name = models.CharField(max_length=150)
    student_contact = models.CharField(max_length=30)
    student_email = models.EmailField()
    student_address = models.TextField()
    course_joined_date = models.DateField()
    course_details = models.TextField()
    image = models.ImageField(upload_to='student_images/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    profile_views = models.IntegerField(default=0)

    def __str__(self):
        return self.student_name
        
    def increment_profile_views(self):
        self.profile_views += 1
        self.save()

class Project(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='projects')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    allow_downloads = models.BooleanField(default=False)
    category = models.CharField(default='Other', max_length=100)
    output_link = models.URLField(blank=True)
    project_link = models.URLField(blank=True)
    tags = models.CharField(blank=True, max_length=200)
    visibility = models.CharField(choices=[('Public', 'Public'), ('Private', 'Private')], default='Public', max_length=20)
    screenshot = models.ImageField(upload_to='project_screenshots/', null=True, blank=True)

    def __str__(self):
        return self.title

    def view_count(self):
        return self.views.count()
        
    def like_count(self):
        return self.likes.count()
        
    def is_liked_by(self, user):
        return self.likes.filter(user=user).exists()

class ProjectView(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

class ProjectLike(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='likes')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'user')

class StudentFollow(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    following = models.ForeignKey(StudentProfile, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f"{self.follower.username} follows {self.following.student_name} ({self.status})"
        
    def accept(self):
        self.status = 'accepted'
        self.save()
        
    def reject(self):
        self.status = 'rejected'
        self.save()

class HiringProcess(models.Model):
    recruiter = models.ForeignKey(RecruiterProfile, on_delete=models.CASCADE, related_name='hiring_processes')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='hiring_processes')
    job_title = models.CharField(max_length=200)
    message = models.TextField()
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.recruiter.company_name} - {self.student.student_name} - {self.job_title}"

class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('like', 'Project Like'),
        ('follow', 'New Follow Request'),
        ('follow_accepted', 'Follow Request Accepted'),
        ('hire', 'Hire Request'),
    )

    recipient = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    # Optional link to a HiringProcess (if this notification represents a hire request)
    hiring_process = models.ForeignKey('HiringProcess', on_delete=models.CASCADE, null=True, blank=True)
    # Optional JSON/text payload for extensible data (job title / message, etc.)
    data = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        if self.notification_type == 'like':
            return f"{self.sender.username} liked your project {self.project.title}"
        elif self.notification_type == 'hire':
            return f"{self.sender.username} wants to hire you for project {self.project.title}"
        return f"{self.sender.username} started following you"
