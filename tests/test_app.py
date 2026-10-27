from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def api_client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr(app_module, "activities", deepcopy(app_module.activities))
    return TestClient(app_module.app)


def test_root_redirects_to_activity_page(api_client: TestClient) -> None:
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = api_client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_details(api_client: TestClient) -> None:
    # Arrange
    expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

    # Act
    response = api_client.get("/activities")

    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert activities["Chess Club"]["participants"] == expected_participants
    assert activities["Basketball Club"]["participants"] == []


def test_signup_adds_participant(api_client: TestClient) -> None:
    # Arrange
    activity_name = "Basketball Club"
    email = "new-student@mergington.edu"

    # Act
    response = api_client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    activities_response = api_client.get("/activities")
    assert email in activities_response.json()[activity_name]["participants"]


def test_signup_rejects_duplicate_participant(api_client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = api_client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_rejects_unknown_activity(api_client: TestClient) -> None:
    # Arrange
    activity_name = "Unknown Club"
    email = "new-student@mergington.edu"

    # Act
    response = api_client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_requires_email(api_client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"

    # Act
    response = api_client.post(f"/activities/{activity_name}/signup")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["query", "email"]


def test_remove_participant_unregisters_student(api_client: TestClient) -> None:
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = api_client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    activities_response = api_client.get("/activities")
    assert email not in activities_response.json()[activity_name]["participants"]


def test_remove_participant_rejects_unregistered_student(
    api_client: TestClient,
) -> None:
    # Arrange
    activity_name = "Basketball Club"
    email = "not-signed-up@mergington.edu"

    # Act
    response = api_client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_remove_participant_rejects_unknown_activity(
    api_client: TestClient,
) -> None:
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = api_client.delete(
        f"/activities/{activity_name}/participants", params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"