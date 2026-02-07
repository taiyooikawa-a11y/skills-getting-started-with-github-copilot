"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Provide a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    activities.clear()
    activities.update({
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Tennis Club": {
            "description": "Learn tennis skills and compete in friendly matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 16,
            "participants": ["alex@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Join our competitive basketball team for practice and games",
            "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 15,
            "participants": ["james@mergington.edu", "maya@mergington.edu"]
        },
        "Drama Club": {
            "description": "Perform in theatrical productions and develop acting skills",
            "schedule": "Thursdays and Saturdays, 2:00 PM - 4:00 PM",
            "max_participants": 25,
            "participants": ["isabella@mergington.edu"]
        },
        "Painting Studio": {
            "description": "Explore visual arts through painting and drawing techniques",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 18,
            "participants": ["noah@mergington.edu", "ava@mergington.edu"]
        },
        "Debate Team": {
            "description": "Develop public speaking and argumentation skills through competitive debate",
            "schedule": "Mondays, 4:00 PM - 5:30 PM",
            "max_participants": 14,
            "participants": ["lucas@mergington.edu"]
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts through hands-on activities",
            "schedule": "Fridays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["harper@mergington.edu", "ethan@mergington.edu"]
        }
    })
    yield
    activities.clear()


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert len(data) == 9

    def test_get_activities_returns_activity_details(self, client):
        """Test that activities include all required fields"""
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_returns_participants(self, client):
        """Test that participants list is correctly returned"""
        response = client.get("/activities")
        data = response.json()
        chess_participants = data["Chess Club"]["participants"]
        
        assert len(chess_participants) == 2
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was actually added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_student_already_registered(self, client):
        """Test signup when student is already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_full(self, client):
        """Test signup when activity is at max capacity"""
        # Create an activity with max 2 participants and 2 already registered
        response = client.post(
            "/activities/Tennis Club/signup?email=student1@mergington.edu"
        )
        assert response.status_code == 200
        
        # Fill up the Tennis Club (starts with 1, max is 16, so we need to fill it)
        # Let's use a smaller example: Debate Team has max 14 and 1 participant
        for i in range(13):
            client.post(
                f"/activities/Debate Team/signup?email=student{i}@mergington.edu"
            )
        
        # Now Debate Team should be full
        response = client.post(
            "/activities/Debate Team/signup?email=overfull@mergington.edu"
        )
        assert response.status_code == 400
        assert "full" in response.json()["detail"]

    def test_signup_updates_participant_count(self, client):
        """Test that participant count increases after signup"""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Programming Class"]["participants"])
        
        client.post(
            "/activities/Programming Class/signup?email=newstudent@mergington.edu"
        )
        
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Programming Class"]["participants"])
        
        assert final_count == initial_count + 1


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        response = client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        
        # Verify student was actually removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_registered(self, client):
        """Test unregister when student is not registered"""
        response = client.post(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_unregister_updates_participant_count(self, client):
        """Test that participant count decreases after unregister"""
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()["Chess Club"]["participants"])
        
        client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        final_response = client.get("/activities")
        final_count = len(final_response.json()["Chess Club"]["participants"])
        
        assert final_count == initial_count - 1

    def test_unregister_then_signup_again(self, client):
        """Test that a student can signup again after unregistering"""
        # Unregister
        client.post(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        
        # Sign up again
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        
        # Verify student is in the list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" in activities_data["Chess Club"]["participants"]


class TestIntegrationScenarios:
    """Integration tests for complex scenarios"""

    def test_multiple_signups_and_unregister(self, client):
        """Test multiple signup and unregister operations"""
        # Sign up multiple students
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/Painting Studio/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Check they're all registered
        response = client.get("/activities")
        participants = response.json()["Painting Studio"]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister some
        client.post(
            "/activities/Painting Studio/unregister?email=student1@mergington.edu"
        )
        
        # Check one was removed
        response = client.get("/activities")
        participants = response.json()["Painting Studio"]["participants"]
        assert "student1@mergington.edu" not in participants
        assert "student2@mergington.edu" in participants
        assert "student3@mergington.edu" in participants

    def test_available_spots_calculation(self, client):
        """Test that spots left calculation is correct"""
        response = client.get("/activities")
        drama_club = response.json()["Drama Club"]
        
        # Drama Club has max 25, 1 participant initially
        initial_spots = drama_club["max_participants"] - len(drama_club["participants"])
        assert initial_spots == 24
        
        # Sign up a student
        client.post(
            "/activities/Drama Club/signup?email=newstudent@mergington.edu"
        )
        
        # Check spots decreased
        response = client.get("/activities")
        drama_club = response.json()["Drama Club"]
        new_spots = drama_club["max_participants"] - len(drama_club["participants"])
        assert new_spots == initial_spots - 1
