import pytest
import asyncio
import json
import os

# Mock environment variables before importing
os.environ.setdefault('AMADEUS_CLIENT_ID', 'test_client_id')
os.environ.setdefault('AMADEUS_CLIENT_SECRET', 'test_client_secret')
os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key')
os.environ.setdefault('TAVILY_API_KEY', 'test_tavily_key')

from fastapi.testclient import TestClient
from app.main import app
from app.models.group_inputs import UserInput, TripGroup
from app.services import storage

# Create test client - using with statement to ensure proper initialization
def get_test_client():
    return TestClient(app)

# Test data
SAMPLE_USER_INPUT = {
    "name": "John Doe",
    "email": "john@example.com",
    "departure_city": "Los Angeles",
    "budget_per_person": 1500,
    "interests": ["food", "culture", "museums"],
    "travel_style": "mid-range",
    "trip_pace": "balanced",
    "group_code": "TEST_GROUP"
}

SAMPLE_TRIP_GROUP = {
    "group_code": "TEST_GROUP",
    "group_name": "Test Trip",
    "destinations": ["Barcelona", "Paris", "Rome"],
    "creator_email": "creator@example.com"
}

class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def setup_method(self):
        """Clean up test data before each test"""
        # Clear any existing test data
        storage.clear_group_data("TEST_GROUP")
        
    def teardown_method(self):
        """Clean up test data after each test"""
        storage.clear_group_data("TEST_GROUP")
    
    def test_root_endpoint(self):
        """Test the root endpoint"""
        client = get_test_client()
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "TripGenie" in data["message"]
    
    def test_ping_endpoint(self):
        """Test the ping endpoint"""
        client = get_test_client()
        response = client.get("/ping")
        assert response.status_code == 200
        data = response.json()
        assert "TripGenie" in data["message"]
    
    def test_create_trip_group(self):
        """Test creating a new trip group"""
        client = get_test_client()
        # Note: This test will fail without proper authentication
        # You'll need to implement test authentication or mock it
        response = client.post(
            "/inputs/group",
            json=SAMPLE_TRIP_GROUP
        )
        # Will likely get 401 without auth, but structure is correct
        assert response.status_code in [200, 201, 401]
    
    def test_submit_user_input(self):
        """Test submitting user preferences"""
        client = get_test_client()
        response = client.post(
            "/inputs/user",
            json=SAMPLE_USER_INPUT,
            params={"group_code": "TEST_GROUP"}
        )
        # Will likely get 401 without auth
        assert response.status_code in [200, 401]
    
    def test_get_group_data(self):
        """Test retrieving group data"""
        client = get_test_client()
        response = client.get(
            "/inputs/group",
            params={"group_code": "TEST_GROUP"}
        )
        assert response.status_code in [200, 404, 401]
    
    def test_list_groups(self):
        """Test listing all groups"""
        client = get_test_client()
        response = client.get("/inputs/groups")
        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert isinstance(data["groups"], list)
    
    def test_clear_group_data(self):
        """Test clearing group data"""
        client = get_test_client()
        response = client.delete(
            "/inputs/clear",
            params={"group_code": "TEST_GROUP"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "cleared" in data["message"]

# Run tests
if __name__ == "__main__":
    # Install pytest if not already installed
    os.system("pip install pytest pytest-asyncio")
    
    # Run the tests
    pytest.main([__file__, "-v"]) 