from django.contrib import admin
from .models import StudentProfile, Project, ProjectView, ProjectLike, StudentFollow, Notification, RecruiterProfile

@admin.register(RecruiterProfile)
class RecruiterProfileAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'contact_person', 'email', 'payment_status', 'status', 'created_at')
    list_filter = ('payment_status', 'status', 'created_at')
    list_editable = ('status',)  # Make status editable in the list view
    search_fields = ('company_name', 'contact_person', 'email')
    readonly_fields = ('payment_id', 'payment_status', 'payment_amount', 'created_at')
    
    def formfield_for_choice_field(self, db_field, request, **kwargs):
        if db_field.name == 'status':
            kwargs['choices'] = [('pending', 'Pending'), ('approved', 'Approved')]
        return super().formfield_for_choice_field(db_field, request, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if obj and obj.status == 'approved':
            readonly_fields.append('status')  # Make status read-only if already approved
        return readonly_fields

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'approved':
            return False  # Prevent deletion of approved recruiters
        return True

    def save_model(self, request, obj, form, change):
        if 'status' in form.changed_data:
            if obj.status == 'approved':
                # Set is_staff to True when approving
                obj.user.is_staff = True
                obj.user.save()
            else:
                # Set is_staff to False when moving back to pending
                obj.user.is_staff = False
                obj.user.save()
        super().save_model(request, obj, form, change)

admin.site.register(StudentProfile)
admin.site.register(Project)
admin.site.register(ProjectView)
admin.site.register(ProjectLike)
admin.site.register(StudentFollow)
admin.site.register(Notification)
