from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib import messages
from django.contrib.auth import get_user_model, login, authenticate, logout
from django.views.decorators.http import require_POST

import logging

import students.cognodb as cognodb


User = get_user_model()
logger = logging.getLogger(__name__)


# ============================================================
# HELPERS
# ============================================================

def get_student_id(user):
    """
    Django user 1 -> Neo4j ST00001
    Django user 25 -> Neo4j ST00025
    """
    return f"ST{user.id:05d}"


def get_logged_in_student(request):
    if not request.user.is_authenticated:
        return None, None, None

    user = request.user
    student_id = get_student_id(user)
    student = cognodb.get_student(student_id)

    return user, student_id, student


# ============================================================
# TEST
# ============================================================

def test_cognodb(request):
    try:
        result = cognodb.test_connection()
        return render(
            request,
            "students/test_cognodb.html",
            {"result": result},
        )
    except Exception as e:
        return HttpResponse(
            f"Neo4j connection failed: {e}",
            status=500,
        )


def create_test_student(request):
    student_id = "ST001"
    student = cognodb.create_student(
        student_id,
        "Raja",
        "raja@example.com",
        "Backend developer",
    )

    return HttpResponse(
        f"Student created: {student['name']}"
    )


# ============================================================
# AUTHENTICATION
# ============================================================

def signup_view(request):

    if request.method == "GET":
        return render(request, "students/signup.html")

    name = request.POST.get("name", "").strip()
    email = request.POST.get("email", "").strip()
    password = request.POST.get("password", "")
    bio = request.POST.get("bio", "").strip()
    skills_input = request.POST.get("skills", "").strip()
    college_name = request.POST.get("college", "").strip()
    qualification = request.POST.get("qualification", "").strip()
    location = request.POST.get("location", "").strip()

    # -----------------------------
    # BASIC VALIDATION
    # -----------------------------

    if not name:
        messages.error(request, "Name is required.")
        return render(request, "students/signup.html")

    if not email:
        messages.error(request, "Email is required.")
        return render(request, "students/signup.html")

    if not password:
        messages.error(request, "Password is required.")
        return render(request, "students/signup.html")

    if len(password) < 8:
        messages.error(
            request,
            "Password must contain at least 8 characters."
        )
        return render(request, "students/signup.html")

    if User.objects.filter(email__iexact=email).exists():
        messages.error(
            request,
            "Email already exists. Please login instead."
        )
        return render(request, "students/signup.html")

    if User.objects.filter(username__iexact=email).exists():
        messages.error(
            request,
            "Email already exists. Please login instead."
        )
        return render(request, "students/signup.html")

    user = None

    try:

        # -----------------------------
        # STEP 1 — DJANGO ACCOUNT
        # -----------------------------

        print("\n========== SIGNUP START ==========")
        print("STEP 1: Creating Django user...")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )

        print("STEP 1 SUCCESS: Django user created")

        # -----------------------------
        # STEP 2 — STUDENT ID
        # -----------------------------

        print("STEP 2: Getting student ID...")

        student_id = get_student_id(user)

        print("STEP 2 SUCCESS:", student_id)

        # -----------------------------
        # STEP 3 — NEO4J STUDENT
        # -----------------------------

        print("STEP 3: Creating Neo4j student...")

        cognodb.create_student(
            student_id,
            name,
            email,
            bio,
        )

        print("STEP 3 SUCCESS: Neo4j student created")

        # -----------------------------
        # STEP 4 — SKILLS
        # -----------------------------

        print("STEP 4: Processing skills...")

        seen_skills = set()

        for raw_skill in skills_input.split(","):

            skill_name = " ".join(
                raw_skill.strip().split()
            )

            if not skill_name:
                continue

            normalized = skill_name.lower()

            if normalized in seen_skills:
                continue

            seen_skills.add(normalized)

            print("ADDING SKILL:", skill_name)

            cognodb.add_skill_to_student_by_name(
                student_id,
                skill_name,
            )

        print("STEP 4 SUCCESS: Skills processed")

        # -----------------------------
        # STEP 5 — COLLEGE
        # -----------------------------

        print("STEP 5: Processing college...")

        if college_name:

            print("Creating/finding college:", college_name)

            college_id = cognodb.make_college_id(
                college_name
            )

            print("College ID:", college_id)

            cognodb.add_student_college(
                student_id,
                college_id,
            )

        print("STEP 5 SUCCESS: College processed")

        # -----------------------------
        # STEP 6 — OTHER DETAILS
        # -----------------------------

        print("STEP 6: Processing other profile details...")

        # Keep your existing qualification/location
        # code here exactly as you already have it.

        print("STEP 6 SUCCESS")

        # -----------------------------
        # LOGIN
        # -----------------------------

        print("STEP 7: Logging user in...")

        login(request, user)

        messages.success(
            request,
            "Account created successfully!"
        )

        print("========== SIGNUP SUCCESS ==========\n")

        return redirect("students:dashboard")

    except Exception as e:

        print("\n========== SIGNUP FAILED ==========")
        print("ERROR TYPE:", type(e).__name__)
        print("ERROR:", repr(e))
        print("===================================\n")

        # Remove half-created Django account
        if user is not None:
            try:
                user.delete()
                print("Django user deleted after failure.")
            except Exception as delete_error:
                print(
                    "Could not delete Django user:",
                    repr(delete_error)
                )

        messages.error(
            request,
            f"Signup failed: {type(e).__name__}: {e}"
        )

        return render(
            request,
            "students/signup.html"
        )

def login_view(request):

    if request.method == "GET":
        return render(
            request,
            "students/login.html",
        )

    email = request.POST.get(
        "email",
        "",
    ).strip().lower()

    password = request.POST.get(
        "password",
        "",
    )

    user = authenticate(
        request,
        username=email,
        password=password,
    )

    if user is not None:

        login(request, user)

        messages.success(
            request,
            "Login successful.",
        )

        return redirect(
            "students:dashboard"
        )

    messages.error(
        request,
        "Invalid email or password.",
    )

    return render(
        request,
        "students/login.html",
    )


def logout_view(request):
    logout(request)

    messages.success(
        request,
        "You have been logged out.",
    )

    return redirect(
        "students:login"
    )


# ============================================================
# PROFILE
# ============================================================

def profile_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    skills = cognodb.get_student_skills(student_id)
    college = cognodb.get_student_college(student_id)
    projects = cognodb.get_student_projects(student_id)

    return render(
        request,
        "students/profile.html",
        {
            "student": student,
            "skills": skills,
            "college": college,
            "projects": projects,
        },
    )


def edit_profile_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    if request.method == "POST":

        name = request.POST.get(
            "name",
            "",
        ).strip()

        bio = request.POST.get(
            "bio",
            "",
        ).strip()

        college_name = request.POST.get(
            "college",
            "",
        ).strip()

        location = request.POST.get(
            "location",
            "",
        ).strip()

        skills_input = request.POST.get(
            "skills",
            "",
        )

        if not name:
            messages.error(
                request,
                "Name is required.",
            )
            return redirect("students:profile")

        cognodb.update_student(
            student_id,
            name,
            user.email,
            bio,
        )

        # Add new skills without creating duplicate Skill nodes.
        seen_skills = set()

        for raw_skill in skills_input.split(","):

            skill_name = " ".join(
                raw_skill.strip().split()
            )

            if not skill_name:
                continue

            normalized = skill_name.lower()

            if normalized in seen_skills:
                continue

            seen_skills.add(normalized)

            cognodb.add_skill_to_student_by_name(
                student_id,
                skill_name,
            )

        if college_name:

            college_id = cognodb.make_college_id(
                college_name
            )

            cognodb.get_or_create_college(
                college_id,
                college_name,
                location,
            )

            cognodb.update_college_for_student(
                student_id,
                college_id,
            )

        messages.success(
            request,
            "Profile updated successfully.",
        )

        return redirect(
            "students:profile"
        )

    skills = cognodb.get_student_skills(student_id)
    college = cognodb.get_student_college(student_id)
    projects = cognodb.get_student_projects(student_id)

    return render(
        request,
        "students/edit_profile.html",
        {
            "student": student,
            "skills": skills,
            "college": college,
            "projects": projects,
            "email": user.email,
        },
    )


# ============================================================
# PROJECTS
# ============================================================

def create_project_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    if request.method == "POST":

        project_name = request.POST.get(
            "project_name",
            "",
        ).strip()

        description = request.POST.get(
            "description",
            "",
        ).strip()

        if not project_name:
            messages.error(
                request,
                "Project name is required.",
            )

            return render(
                request,
                "students/create_project.html",
                {"student": student},
            )

        project_id = (
            f"PR{student_id[2:]}-"
            f"{project_name.lower().replace(' ', '-')}"
        )

        cognodb.create_project(
            project_id,
            project_name,
            description,
        )

        cognodb.add_student_project(
            student_id,
            project_id,
        )

        messages.success(
            request,
            "Project created successfully.",
        )

        return redirect(
            "students:profile"
        )

    return render(
        request,
        "students/create_project.html",
        {"student": student},
    )


@require_POST
def project_delete_view(request, project_id):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    projects = cognodb.get_student_projects(student_id)

    project_exists = any(
        project.get("project_id") == project_id
        for project in projects
    )

    if not project_exists:
        messages.error(
            request,
            "Project not found.",
        )
        return redirect(
            "students:profile"
        )

    cognodb.delete_project(project_id)

    messages.success(
        request,
        "Project deleted successfully.",
    )

    return redirect(
        "students:profile"
    )


# ============================================================
# DASHBOARD
# ============================================================

def dashboard_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    skills = cognodb.get_student_skills(student_id)
    college = cognodb.get_student_college(student_id)
    projects = cognodb.get_student_projects(student_id)

    # --------------------------------------------------------
    # Search
    # --------------------------------------------------------

    query = request.GET.get(
        "q",
        "",
    ).strip()

    search_results = []

    if query:
        search_results = cognodb.search_students(
            student_id,
            query,
        )

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    skill_recommendations = cognodb.get_skill_recommendations(
        student_id,
    )

    college_recommendations = cognodb.get_same_college_students(
        student_id,
    )

    # --------------------------------------------------------
    # Incoming requests
    # --------------------------------------------------------

    connection_requests = cognodb.get_pending_requests(
        student_id,
    )

    return render(
        request,
        "students/dashboard.html",
        {
            "student": student,
            "skills": skills,
            "college": college,
            "projects": projects,

            "query": query,
            "search_results": search_results,

            "skill_recommendations": skill_recommendations,
            "college_recommendations": college_recommendations,

            "connection_requests": connection_requests,
        },
    )


# ============================================================
# RECOMMENDATION PAGES
# ============================================================

def skill_recommendation_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    recommendations = cognodb.get_skill_recommendations(
        student_id,
    )

    return render(
        request,
        "students/skill_recommendation.html",
        {
            "student": student,
            "recommended_students": recommendations,
        },
    )


def college_recommendation_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    recommendations = cognodb.get_same_college_students(
        student_id,
    )

    return render(
        request,
        "students/college_recommendation.html",
        {
            "student": student,
            "same_college_students": recommendations,
        },
    )


# ============================================================
# CONNECTION REQUESTS
# ============================================================

@require_POST
def send_request_view(request, target_student_id):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if student_id == target_student_id:
        messages.error(
            request,
            "You cannot send a request to yourself.",
        )
        return redirect("students:dashboard")

    target_student = cognodb.get_student(
        target_student_id
    )

    if not target_student:
        messages.error(
            request,
            "Target student profile not found.",
        )
        return redirect("students:dashboard")

    try:

        result = cognodb.send_connection_request(
            student_id,
            target_student_id,
        )

        if result:
            messages.success(
                request,
                "Connection request sent.",
            )
        else:
            messages.error(
                request,
                "Unable to send connection request.",
            )

    except Exception as e:

        messages.error(
            request,
            f"Unable to send request: {e}",
        )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "students:dashboard",
        )
    )


def request_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    connection_requests = cognodb.get_pending_requests(
        student_id
    )

    return render(
        request,
        "students/connection_requests.html",
        {
            "student": student,
            "connection_requests": connection_requests,
        },
    )


@require_POST
def accept_request_view(request, requester_student_id):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if student_id == requester_student_id:
        messages.error(
            request,
            "Invalid request.",
        )
        return redirect("students:request")

    try:

        accepted = cognodb.accept_connection(
            requester_student_id,
            student_id,
        )

        if accepted:
            messages.success(
                request,
                "Connection request accepted.",
            )
        else:
            messages.error(
                request,
                "Request was not found or was already handled.",
            )

    except Exception as e:

        messages.error(
            request,
            f"Unable to accept request: {e}",
        )

    return redirect(
        "students:request"
    )


@require_POST
def reject_request_view(request, requester_student_id):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if student_id == requester_student_id:
        messages.error(
            request,
            "Invalid request.",
        )
        return redirect("students:request")

    try:

        rejected = cognodb.reject_connection(
            requester_student_id,
            student_id,
        )

        if rejected:
            messages.success(
                request,
                "Connection request rejected.",
            )
        else:
            messages.error(
                request,
                "Request was not found or was already handled.",
            )

    except Exception as e:

        messages.error(
            request,
            f"Unable to reject request: {e}",
        )

    return redirect(
        "students:request"
    )


# ============================================================
# CONNECTIONS
# ============================================================

def connections_view(request):

    user, student_id, student = get_logged_in_student(request)

    if user is None:
        return redirect("students:login")

    if not student:
        return HttpResponse(
            f"Student profile not found for {student_id}.",
            status=404,
        )

    connections = cognodb.get_connections(
        student_id
    )

    return render(
        request,
        "students/connections.html",
        {
            "student": student,
            "connections": connections,
        },
    )       