import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        activity_name: activity["participants"][:]
        for activity_name, activity in activities.items()
    }

    yield

    for activity_name, participants in original_participants.items():
        activities[activity_name]["participants"] = participants


def test_root_redirects_to_static_index():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_details():
    response = client.get("/activities")

    assert response.status_code == 200
    activity = response.json()["Chess Club"]
    assert activity["description"]
    assert activity["schedule"]
    assert activity["max_participants"] == 12
    assert activity["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_email_to_activity():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }

    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_rejects_duplicate_email():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_rejects_unknown_activity():
    response = client.post(
        "/activities/Unknown Club/signup?email=student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_requires_email():
    response = client.post("/activities/Chess Club/signup")

    assert response.status_code == 422


def test_unregister_participant_removes_email_from_activity():
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    client.post(f"/activities/{activity_name}/signup?email={email}")

    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}",
        "participants": [
            "michael@mergington.edu",
            "daniel@mergington.edu",
        ],
    }
    assert email not in response.json()["participants"]

    assert email not in client.get("/activities").json()[activity_name]["participants"]


def test_unregister_rejects_unknown_activity():
    response = client.delete(
        "/activities/Unknown Club/unregister?email=student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_unregistered_email():
    response = client.delete(
        "/activities/Chess Club/unregister?email=student@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not registered for this activity"
    }
