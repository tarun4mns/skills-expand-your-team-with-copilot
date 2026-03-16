"""
API flow tests for the Mergington High School extracurricular activities system.

Covers the core end-to-end flow:
  1. Listing and filtering activities
  2. Teacher authentication
  3. Signing a student up for an activity
  4. Unregistering a student from an activity
"""


# ---------------------------------------------------------------------------
# Activities endpoints
# ---------------------------------------------------------------------------

def test_get_all_activities(client):
    """GET /activities returns a non-empty dict with known activity names."""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    assert "Chess Club" in data


def test_get_activities_filter_by_day(client):
    """GET /activities?day=Monday only returns activities scheduled on Monday."""
    response = client.get("/activities?day=Monday")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for activity in data.values():
        assert "Monday" in activity["schedule_details"]["days"]


def test_get_activities_filter_by_time(client):
    """GET /activities with start_time/end_time returns activities in that window."""
    response = client.get("/activities?start_time=15:00&end_time=17:30")
    assert response.status_code == 200
    data = response.json()
    for activity in data.values():
        assert activity["schedule_details"]["start_time"] >= "15:00"
        assert activity["schedule_details"]["end_time"] <= "17:30"


def test_get_available_days(client):
    """GET /activities/days returns a sorted list of day strings."""
    response = client.get("/activities/days")
    assert response.status_code == 200
    days = response.json()
    assert isinstance(days, list)
    assert len(days) > 0
    assert "Monday" in days
    assert "Saturday" in days


# ---------------------------------------------------------------------------
# Authentication endpoints
# ---------------------------------------------------------------------------

def test_login_success(client):
    """POST /auth/login returns teacher info on valid credentials."""
    response = client.post("/auth/login?username=mrodriguez&password=art123")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "mrodriguez"
    assert data["display_name"] == "Ms. Rodriguez"
    assert "password" not in data


def test_login_wrong_password(client):
    """POST /auth/login returns 401 when the password is incorrect."""
    response = client.post("/auth/login?username=mrodriguez&password=wrong")
    assert response.status_code == 401


def test_login_unknown_user(client):
    """POST /auth/login returns 401 for an unknown username."""
    response = client.post("/auth/login?username=nobody&password=art123")
    assert response.status_code == 401


def test_check_session_valid(client):
    """GET /auth/check-session returns teacher info for a valid username."""
    response = client.get("/auth/check-session?username=mchen")
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "mchen"
    assert data["display_name"] == "Mr. Chen"


def test_check_session_invalid(client):
    """GET /auth/check-session returns 404 for an unknown username."""
    response = client.get("/auth/check-session?username=ghost")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Full signup / unregister flow
# ---------------------------------------------------------------------------

def test_signup_requires_teacher(client):
    """POST /activities/{name}/signup without a teacher returns 401."""
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": "student@mergington.edu"},
    )
    assert response.status_code == 401


def test_signup_unknown_activity(client):
    """POST /activities/{name}/signup for a non-existent activity returns 404."""
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "student@mergington.edu", "teacher_username": "mrodriguez"},
    )
    assert response.status_code == 404


def test_full_signup_and_unregister_flow(client):
    """
    Full flow:
      1. Login as a teacher.
      2. Sign a new student up for Chess Club.
      3. Verify the student appears in the participants list.
      4. Unregister the student.
      5. Verify the student is removed.
    """
    # Step 1 – authenticate
    login_response = client.post("/auth/login?username=mrodriguez&password=art123")
    assert login_response.status_code == 200

    email = "newstudent@mergington.edu"
    activity = "Chess Club"

    # Step 2 – sign up
    signup_response = client.post(
        f"/activities/{activity}/signup",
        params={"email": email, "teacher_username": "mrodriguez"},
    )
    assert signup_response.status_code == 200
    assert email in signup_response.json()["message"]

    # Step 3 – verify enrollment
    activities = client.get("/activities").json()
    assert email in activities[activity]["participants"]

    # Step 4 – unregister
    unregister_response = client.post(
        f"/activities/{activity}/unregister",
        params={"email": email, "teacher_username": "mrodriguez"},
    )
    assert unregister_response.status_code == 200

    # Step 5 – verify removal
    activities = client.get("/activities").json()
    assert email not in activities[activity]["participants"]


def test_duplicate_signup_rejected(client):
    """Signing up a student who is already enrolled returns 400."""
    existing_email = "michael@mergington.edu"  # pre-seeded participant
    response = client.post(
        "/activities/Chess Club/signup",
        params={"email": existing_email, "teacher_username": "mrodriguez"},
    )
    assert response.status_code == 400


def test_unregister_not_enrolled_rejected(client):
    """Unregistering a student who is not enrolled returns 400."""
    response = client.post(
        "/activities/Chess Club/unregister",
        params={"email": "noone@mergington.edu", "teacher_username": "mrodriguez"},
    )
    assert response.status_code == 400
