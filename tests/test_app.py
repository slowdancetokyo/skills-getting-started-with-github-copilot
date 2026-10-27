import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static_index(reset_activities):
    with TestClient(app) as client:
        response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(reset_activities):
    with TestClient(app) as client:
        response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_student_and_persists(reset_activities):
    email = "newstudent@mergington.edu"
    activity_name = "Judo Class"

    with TestClient(app) as client:
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

        assert response.status_code == 200
        assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
        assert email in activities[activity_name]["participants"]


def test_signup_raises_400_for_duplicate_participant(reset_activities):
    email = "michael@mergington.edu"
    activity_name = "Chess Club"

    with TestClient(app) as client:
        response = client.post(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

    assert response.status_code == 400
    assert response.json() == {"detail": "Student is already signed up"}


def test_signup_raises_404_for_unknown_activity(reset_activities):
    with TestClient(app) as client:
        response = client.post(
            "/activities/Unknown Activity/signup",
            params={"email": "student@mergington.edu"},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_removes_signed_up_student(reset_activities):
    email = "newstudent@mergington.edu"
    activity_name = "Basketball Team"
    activities[activity_name]["participants"].append(email)

    with TestClient(app) as client:
        response = client.delete(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

        assert response.status_code == 200
        assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
        assert email not in activities[activity_name]["participants"]


def test_unregister_raises_404_for_student_not_signed_up(reset_activities):
    email = "notregistered@mergington.edu"
    activity_name = "Basketball Team"

    with TestClient(app) as client:
        response = client.delete(
            f"/activities/{quote(activity_name)}/signup",
            params={"email": email},
        )

    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
