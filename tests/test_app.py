"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Create a test client
client = TestClient(app)

# Store original activities to restore after each test
original_activities = None


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test"""
    global original_activities
    
    # Deep copy activities before first test
    if original_activities is None:
        original_activities = {
            name: {
                "description": details["description"],
                "schedule": details["schedule"],
                "max_participants": details["max_participants"],
                "participants": details["participants"].copy()
            }
            for name, details in activities.items()
        }
    
    # Reset activities before each test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()
    
    yield
    
    # Reset activities after each test
    for name in activities:
        activities[name]["participants"] = original_activities[name]["participants"].copy()


class TestGetActivities:
    """Test getting activities"""
    
    def test_get_activities(self):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert isinstance(data, dict)
        assert "Basketball Team" in data
        assert "Swimming Team" in data
        
    def test_get_activities_contains_required_fields(self):
        """Test that activities contain required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Test signup functionality"""
    
    def test_signup_success(self):
        """Test successful signup"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify participant was added
        assert "newstudent@mergington.edu" in activities["Basketball Team"]["participants"]
    
    def test_signup_nonexistent_activity(self):
        """Test signup for activity that doesn't exist"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_student(self):
        """Test signup for activity student is already in"""
        existing_email = activities["Basketball Team"]["participants"][0]
        response = client.post(
            f"/activities/Basketball Team/signup?email={existing_email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_multiple_activities(self):
        """Test student can sign up for multiple activities"""
        email = "multistudent@mergington.edu"
        
        # Sign up for first activity
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Sign up for second activity
        response2 = client.post(
            f"/activities/Swimming Team/signup?email={email}"
        )
        assert response2.status_code == 200
        
        # Verify student is in both activities
        assert email in activities["Basketball Team"]["participants"]
        assert email in activities["Swimming Team"]["participants"]


class TestUnregister:
    """Test unregister functionality"""
    
    def test_unregister_success(self):
        """Test successful unregister"""
        email = activities["Basketball Team"]["participants"][0]
        
        response = client.delete(
            f"/activities/Basketball Team/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant was removed
        assert email not in activities["Basketball Team"]["participants"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregister from activity that doesn't exist"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_not_registered_student(self):
        """Test unregister for student not in activity"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notstudent@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_then_signup_again(self):
        """Test student can unregister and sign up again"""
        email = "testme@mergington.edu"
        
        # Sign up
        response1 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response1.status_code == 200
        assert email in activities["Basketball Team"]["participants"]
        
        # Unregister
        response2 = client.delete(
            f"/activities/Basketball Team/unregister?email={email}"
        )
        assert response2.status_code == 200
        assert email not in activities["Basketball Team"]["participants"]
        
        # Sign up again
        response3 = client.post(
            f"/activities/Basketball Team/signup?email={email}"
        )
        assert response3.status_code == 200
        assert email in activities["Basketball Team"]["participants"]


class TestRoot:
    """Test root endpoint"""
    
    def test_root_redirect(self):
        """Test root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
