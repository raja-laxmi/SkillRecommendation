from django.urls import path
from . import views

app_name = "students"

urlpatterns = [

    # Testing
    path(
        "test_cognodb/",
        views.test_cognodb,
        name="test_cognodb"
    ),

    path(
        "create-test-student/",
        views.create_test_student,
        name="create_test_student"
    ),

    # Authentication
    path(
        "signup/",
        views.signup_view,
        name="signup"
    ),

    path(
        "login/",
        views.login_view,
        name="login"
    ),

    path(
        "logout/",
        views.logout_view,
        name="logout"
    ),

    # Dashboard
    path(
        "dashboard/",
        views.dashboard_view,
        name="dashboard"
    ),

    # Profile
    path(
        "profile/",
        views.profile_view,
        name="profile"
    ),

    path(
        "profile/edit/",
        views.edit_profile_view,
        name="edit_profile"
    ),

    # Projects
    path(
        "projects/create/",
        views.create_project_view,
        name="create_project"
    ),

    path(
        "project/<str:project_id>/delete/",
        views.project_delete_view,
        name="delete_project"
    ),

    # Recommendations
    path(
        "recommendations/skills/",
        views.skill_recommendation_view,
        name="skill_recommendation"
    ),

    path(
        "recommendations/college/",
        views.college_recommendation_view,
        name="college_recommendation"
    ),

    # Connections
    path(
        "connections/",
        views.connections_view,
        name="connections"
    ),

    path(
        "connections/send/<str:target_student_id>/",
        views.send_request_view,
        name="send_request"
    ),

    path(
        "connections/requests/",
        views.request_view,
        name="request"
    ),

    path(
        "connections/accept/<str:requester_student_id>/",
        views.accept_request_view,
        name="accept_request"
    ),

    path(
        "connections/reject/<str:requester_student_id>/",
        views.reject_request_view,
        name="reject_request"
    ),
]
        
    
    

