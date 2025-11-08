from django.urls import path

from . import views
from .home_view import home
from .admin_views import (admin_home, admin_projects, admin_profiles, 
                          student_projects_api, student_project_details, public_student_projects)
from .student_views import (student_home, student_projects, delete_project, 
                          record_project_view, toggle_project_like, edit_project, 
                          remove_from_recent_uploads)
from .notification_views import student_project_detail, toggle_follow, notifications, send_hire_notification, notifications_unread_json
from .views import student_profile_view, request_follow, handle_follow_request
from .recruiter_views import (recruiter_register_view, create_recruiter_order, 
                            complete_recruiter_registration, recruiter_home,
                            toggle_save_student, view_student_profile, view_project_details,
                            saved_profiles, initiate_hiring_process, browse_talent, student_projects)

urlpatterns = [
    # Student profile URLs
    path('student/<int:student_id>/profile/', student_profile_view, name='student_profile'),
    path('student/<int:student_id>/request-follow/', request_follow, name='request_follow'),
    path('student/follow-request/<int:follow_id>/', handle_follow_request, name='handle_follow_request'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('add-student/', views.add_student, name='add_student'),
    path('developers/', public_student_projects, name='public_student_projects'),
    path('home/', home, name='home'),
    path('admin-home/', admin_home, name='admin_home'),
    path('admin-projects/', admin_projects, name='admin_projects'),
    path('admin-profiles/', admin_profiles, name='admin_profiles'),
    path('student-projects/<int:student_id>/', student_projects_api, name='student_projects_api'),
    path('student/<int:student_id>/projects/', student_project_details, name='student_project_details'),
    path('student-home/', student_home, name='student_home'),
    path('project/<int:project_id>/like/', toggle_project_like, name='toggle_project_like'),
    path('project/<int:project_id>/delete/', delete_project, name='delete_project'),
    path('project/<int:project_id>/edit/', edit_project, name='edit_project'),
    path('project/<int:project_id>/remove-from-recent/', remove_from_recent_uploads, name='remove_from_recent_uploads'),
    path('project/<int:project_id>/details/', student_project_detail, name='student_project_detail'),
    path('project/<int:project_id>/hire/', send_hire_notification, name='send_hire_notification'),
    path('student/<int:student_id>/follow/', toggle_follow, name='toggle_follow'),
    path('notifications/', notifications, name='notifications'),
    path('notifications/unread-json/', notifications_unread_json, name='notifications_unread_json'),
    path('projects/', student_projects, name='student_projects'),
        path('record-project-view/', record_project_view, name='record_project_view'),
    path('delete-project/<int:project_id>/', delete_project, name='delete_project'),
    path('', views.login_view, name='root'),
    path('recruiter-register/', recruiter_register_view, name='recruiter_register'),
    path('create-recruiter-order/', create_recruiter_order, name='create_recruiter_order'),
    path('complete-recruiter-registration/', complete_recruiter_registration, name='complete_recruiter_registration'),
    path('recruiter-home/', recruiter_home, name='recruiter_home'),
    path('recruiter/student-projects/', student_projects, name='recruiter_student_projects'),
    path('browse/talent/', browse_talent, name='browse_talent'),
    path('saved-profiles/', saved_profiles, name='saved_profiles'),
    path('student/<int:student_id>/save/', toggle_save_student, name='toggle_save_student'),
    path('student/<int:student_id>/recruiter-view/', view_student_profile, name='view_student_profile'),
    path('project/<int:project_id>/recruiter-view/', view_project_details, name='view_project_details'),
    path('student/<int:student_id>/hire/', initiate_hiring_process, name='initiate_hiring_process'),
]
