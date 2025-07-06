import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Mock environment variables before importing
os.environ.setdefault('AMADEUS_CLIENT_ID', 'test_client_id')
os.environ.setdefault('AMADEUS_CLIENT_SECRET', 'test_client_secret')
os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key')
os.environ.setdefault('TAVILY_API_KEY', 'test_tavily_key')

from app.services import storage, auth
from app.services.planner import plan_trip
from app.services.ai_input import get_group_preferences, prepare_ai_input
from app.models.group_inputs import UserInput, TripGroup, Preferences, Availability, Budget
from app.models.auth import User

class TestStorageService:
    """Test storage service functionality"""
    
    def setup_method(self):
        """Set up test with temporary storage"""
        self.test_dir = tempfile.mkdtemp()
        self.original_storage_dir = storage.STORAGE_DIR
        storage.STORAGE_DIR = self.test_dir
        
        # Clear any existing test data
        storage.clear_group_data("TEST_GROUP")
        storage.clear_group_data("TRIP_TEST")
        
    def teardown_method(self):
        """Clean up test directory"""
        # Clean up test data
        storage.clear_group_data("TEST_GROUP") 
        storage.clear_group_data("TRIP_TEST")
        storage.STORAGE_DIR = self.original_storage_dir
        
    def test_create_trip_group(self):
        """Test creating a new trip group"""
        trip_group = TripGroup(
            group_code="TEST_GROUP",
            destinations=["Barcelona", "Paris"],
            creator_email="test@example.com",
            created_at="2024-01-01T00:00:00"
        )
        
        result = storage.create_trip_group(trip_group)
        assert result is not None
        assert result.group_code == "TEST_GROUP"
        assert len(result.destinations) == 2
        
    def test_add_user_to_group(self):
        """Test adding user to group"""
        user_input = UserInput(
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            preferences=Preferences(
                vibe=["culture"],
                interests=["food", "culture"],
                departure_airports=["LAX"],
                budget=Budget(min=1000, max=2000),
                trip_duration=7,
                travel_style="balanced",
                pace="balanced"
            ),
            availability=Availability(dates=["2024-06-15", "2024-06-16"])
        )
        
        result = storage.add_user_to_group(user_input, "TEST_GROUP")
        assert result is not None
        
        # Verify user was added
        group_data = storage.get_group_data("TEST_GROUP")
        assert len(group_data) == 1
        assert group_data[0].email == "john@example.com"
        
    def test_get_group_data(self):
        """Test retrieving group data"""
        # First add some data
        user_input = UserInput(
            name="Jane Smith",
            email="jane@example.com",
            phone="+1234567890",
            preferences=Preferences(
                vibe=["culture"],
                interests=["museums", "shopping"],
                departure_airports=["JFK"],
                budget=Budget(min=1500, max=2500),
                trip_duration=5,
                travel_style="balanced",
                pace="balanced"
            ),
            availability=Availability(dates=["2024-07-01", "2024-07-02"])
        )
        
        storage.add_user_to_group(user_input, "TEST_GROUP")
        
        # Test retrieval
        group_data = storage.get_group_data("TEST_GROUP")
        assert len(group_data) == 1
        assert group_data[0].name == "Jane Smith"
        
    def test_clear_group_data(self):
        """Test clearing specific group data"""
        user_input = UserInput(
            name="Test User",
            email="test@example.com",
            phone="+1234567890",
            preferences=Preferences(
                vibe=["party"],
                interests=["nightlife"],
                departure_airports=["ORD"],
                budget=Budget(min=800, max=1500),
                trip_duration=3,
                travel_style="budget",
                pace="fast"
            ),
            availability=Availability(dates=["2024-08-01"])
        )
        
        storage.add_user_to_group(user_input, "TEST_GROUP")
        
        # Verify data exists
        group_data = storage.get_group_data("TEST_GROUP")
        assert len(group_data) == 1
        
        # Clear data
        storage.clear_group_data("TEST_GROUP")
        
        # Verify data is cleared
        group_data = storage.get_group_data("TEST_GROUP")
        assert len(group_data) == 0
        
    def test_get_trip_group(self):
        """Test retrieving trip group"""
        trip_group = TripGroup(
            group_code="TRIP_TEST",
            destinations=["Tokyo", "Kyoto"],
            creator_email="creator@example.com",
            created_at="2024-01-01T00:00:00"
        )
        
        storage.create_trip_group(trip_group)
        
        # Test retrieval
        retrieved_group = storage.get_trip_group("TRIP_TEST")
        assert retrieved_group is not None
        assert retrieved_group.group_code == "TRIP_TEST"
        assert len(retrieved_group.destinations) == 2


class TestAuthService:
    """Test authentication service functionality"""
    
    def setup_method(self):
        """Set up test with temporary auth storage"""
        self.test_dir = tempfile.mkdtemp()
        self.original_users_file = auth.USERS_FILE
        self.original_trips_file = auth.TRIPS_FILE
        auth.USERS_FILE = os.path.join(self.test_dir, "users.json")
        auth.TRIPS_FILE = os.path.join(self.test_dir, "trips.json")
        
    def teardown_method(self):
        """Clean up test directory"""
        auth.USERS_FILE = self.original_users_file
        auth.TRIPS_FILE = self.original_trips_file
    
    def test_create_user(self):
        """Test creating a new user"""
        user = auth.create_user(
            email="test@example.com",
            password="testpass123",
            name="Test User"
        )
        
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.id is not None
    
    def test_authenticate_user(self):
        """Test user authentication"""
        # Create user first
        auth.create_user(
            email="auth@example.com",
            password="authpass123",
            name="Auth User"
        )
        
        # Test authentication
        user = auth.authenticate_user("auth@example.com", "authpass123")
        assert user is not None
        assert user.email == "auth@example.com"
        
        # Test wrong password
        user = auth.authenticate_user("auth@example.com", "wrongpass")
        assert user is None
    
    def test_add_user_to_trip(self):
        """Test adding user to trip"""
        # Create user first
        user = auth.create_user(
            email="trip@example.com",
            password="trippass123",
            name="Trip User"
        )
        
        auth.add_user_to_trip(user.id, "TRIP_123", role="member")
        
        # Verify user was added to trip
        user_trips = auth.get_user_trips(user.id)
        assert len(user_trips) == 1
        assert user_trips[0].groupCode == "TRIP_123"
        assert user_trips[0].role == "member"
    
    def test_get_user_trips(self):
        """Test retrieving user trips"""
        # Create user
        user = auth.create_user(
            email="trips@example.com",
            password="tripspass123",
            name="Trips User"
        )
        
        # Add multiple trips
        auth.add_user_to_trip(user.id, "TRIP_A", role="creator")
        auth.add_user_to_trip(user.id, "TRIP_B", role="member")
        
        # Retrieve trips
        user_trips = auth.get_user_trips(user.id)
        assert len(user_trips) == 2
        trip_codes = [trip.groupCode for trip in user_trips]
        assert "TRIP_A" in trip_codes
        assert "TRIP_B" in trip_codes


class TestAIInputService:
    """Test AI input processing functionality"""
    
    def test_get_group_preferences(self):
        """Test group preference aggregation"""
        users = [
            UserInput(
                name="User 1",
                email="user1@example.com",
                phone="+1234567890",
                preferences=Preferences(
                    vibe=["culture"],
                    interests=["food", "culture"],
                    departure_airports=["LAX"],
                    budget=Budget(min=1000, max=2000),
                    trip_duration=7,
                    travel_style="balanced",
                    pace="balanced"
                ),
                availability=Availability(dates=["2024-06-15", "2024-06-16"])
            ),
            UserInput(
                name="User 2",
                email="user2@example.com",
                phone="+1234567890",
                preferences=Preferences(
                    vibe=["culture"],
                    interests=["culture", "museums"],
                    departure_airports=["SFO"],
                    budget=Budget(min=1500, max=2500),
                    trip_duration=7,
                    travel_style="balanced",
                    pace="fast"
                ),
                availability=Availability(dates=["2024-06-15", "2024-06-16"])
            )
        ]
        
        preferences = get_group_preferences(users)
        
        # Check that preferences are aggregated
        assert "interests" in preferences
        assert "food" in preferences["interests"]
        assert "culture" in preferences["interests"]
        assert "museums" in preferences["interests"]
        
        # Check budget aggregation
        assert "budget" in preferences
        assert preferences["budget"]["min"] >= 1000
        assert preferences["budget"]["max"] <= 2500
        
    def test_prepare_ai_input(self):
        """Test AI input preparation"""
        tomorrow = datetime.now() + timedelta(days=1)
        week_later = tomorrow + timedelta(days=7)

        users = [
            UserInput(
                name="Test User",
                email="test@example.com",
                phone="+1234567890",
                preferences=Preferences(
                    vibe=["party"],
                    interests=["nightlife", "shopping"],
                    departure_airports=["ORD"],
                    budget=Budget(min=1200, max=2200),
                    trip_duration=5,
                    travel_style="balanced",
                    pace="balanced"
                ),
                availability=Availability(dates=[
                    tomorrow.strftime("%Y-%m-%d"),
                    week_later.strftime("%Y-%m-%d")
                ])
            )
        ]
        
        destinations = ["Barcelona", "Paris"]
        
        ai_input = prepare_ai_input(users, destinations)
        
        # Check that AI input is properly formatted
        assert "destinations" in ai_input
        assert "group_preferences" in ai_input
        assert "trip_constraints" in ai_input
        assert ai_input["destinations"] == destinations


class TestPlannerService:
    """Test trip planning service functionality"""
    
    def setup_method(self):
        """Set up test with temporary storage"""
        self.test_dir = tempfile.mkdtemp()
        self.original_storage_dir = storage.STORAGE_DIR
        storage.STORAGE_DIR = self.test_dir
        
    def teardown_method(self):
        """Clean up test directory"""
        storage.STORAGE_DIR = self.original_storage_dir
    
    @pytest.mark.asyncio
    async def test_plan_trip_with_valid_data(self):
        """Test trip planning with valid user data"""
        # Create trip group first
        trip_group = TripGroup(
            group_code="PLAN_TEST",
            destinations=["Barcelona", "Paris"],
            creator_email="creator@example.com",
            created_at="2024-01-01T00:00:00"
        )
        storage.create_trip_group(trip_group)
        
        # Add users
        user1 = UserInput(
            name="User 1",
            email="user1@example.com",
            phone="+1234567890",
            preferences=Preferences(
                vibe=["culture"],
                interests=["food", "museums"],
                departure_airports=["LAX"],
                budget=Budget(min=1500, max=2500),
                trip_duration=7,
                travel_style="balanced",
                pace="balanced"
            ),
            availability=Availability(dates=["2024-06-15", "2024-06-16"])
        )
        
        user2 = UserInput(
            name="User 2", 
            email="user2@example.com",
            phone="+1234567890",
            preferences=Preferences(
                vibe=["culture"],
                interests=["culture", "art"],
                departure_airports=["SFO"],
                budget=Budget(min=1200, max=2200),
                trip_duration=7,
                travel_style="balanced",
                pace="balanced"
            ),
            availability=Availability(dates=["2024-06-15", "2024-06-16"])
        )
        
        storage.add_user_to_group(user1, "PLAN_TEST")
        storage.add_user_to_group(user2, "PLAN_TEST")
        
        # Mock the travel agent to avoid actual API calls
        with patch('app.services.planner.travel_agent') as mock_agent:
            mock_agent.plan_trip.return_value = {
                "itinerary": "Mock trip plan",
                "destinations": ["Barcelona", "Paris"],
                "estimated_cost": 2000
            }
            
            # Test planning
            result = await plan_trip("PLAN_TEST")
            
            # Check results
            assert result is not None
            assert "itinerary" in result
            assert "destinations" in result
            
    @pytest.mark.asyncio
    async def test_plan_trip_no_destinations(self):
        """Test trip planning when no destinations are set"""
        users = [
            UserInput(
                name="No Dest User",
                email="nodest@example.com",
                phone="+1234567890",
                preferences=Preferences(
                    vibe=["culture"],
                    interests=["food"],
                    departure_airports=["ORD"],
                    budget=Budget(min=1000, max=2000),
                    trip_duration=7,
                    travel_style="balanced",
                    pace="balanced"
                ),
                availability=Availability(dates=["2024-06-15"]),
                group_code="NO_DEST_GROUP"
            )
        ]
        
        # Should handle case where no destinations are provided
        with patch('app.services.planner.travel_agent') as mock_agent:
            mock_agent.plan_trip.return_value = {
                "error": "No destinations provided"
            }
            
            result = await plan_trip("NO_DEST_GROUP")
            
            # Should return error or handle gracefully
            assert result is not None
            
    @pytest.mark.asyncio
    async def test_plan_trip_no_availability(self):
        """Test trip planning when users have no overlapping dates"""
        users = [
            UserInput(
                name="User A",
                email="usera@example.com",
                phone="+1234567890",
                preferences=Preferences(
                    vibe=["culture"],
                    interests=["food"],
                    departure_airports=["BOS"],
                    budget=Budget(min=1000, max=2000),
                    trip_duration=7,
                    travel_style="balanced",
                    pace="balanced"
                ),
                availability=Availability(dates=["2024-06-01", "2024-06-07"])
            ),
            UserInput(
                name="User B",
                email="userb@example.com",
                phone="+1234567890",
                preferences=Preferences(
                    vibe=["culture"],
                    interests=["food"],
                    departure_airports=["SEA"],
                    budget=Budget(min=1000, max=2000),
                    trip_duration=7,
                    travel_style="balanced",
                    pace="balanced"
                ),
                availability=Availability(dates=["2024-07-01", "2024-07-07"])
            )
        ]
        
        # Should handle case where no dates overlap
        with patch('app.services.planner.travel_agent') as mock_agent:
            mock_agent.plan_trip.return_value = {
                "error": "No overlapping availability"
            }
            
            result = await plan_trip("NO_AVAILABILITY_GROUP")
            
            # Should return error or handle gracefully
            assert result is not None


# Integration tests
class TestServiceIntegration:
    """Test services working together in realistic scenarios"""
    
    def setup_method(self):
        """Set up test with temporary storage"""
        self.test_dir = tempfile.mkdtemp()
        self.original_storage_dir = storage.STORAGE_DIR
        self.original_users_file = auth.USERS_FILE
        self.original_trips_file = auth.TRIPS_FILE
        
        storage.STORAGE_DIR = self.test_dir
        auth.USERS_FILE = os.path.join(self.test_dir, "users.json")
        auth.TRIPS_FILE = os.path.join(self.test_dir, "trips.json")
        
    def teardown_method(self):
        """Clean up test directory"""
        storage.STORAGE_DIR = self.original_storage_dir
        auth.USERS_FILE = self.original_users_file
        auth.TRIPS_FILE = self.original_trips_file
    
    @pytest.mark.asyncio
    async def test_complete_user_journey(self):
        """Test a complete user journey from group creation to trip planning"""
        
        # Step 1: Create trip group
        trip_group = TripGroup(
            group_code="INTEGRATION_TEST",
            destinations=["Barcelona", "Paris"],
            creator_email="creator@example.com",
            created_at="2024-01-01T00:00:00"
        )
        storage.create_trip_group(trip_group)
        
        # Step 2: Users join the group
        user1 = UserInput(
            name="Alice Smith",
            email="alice@example.com",
            phone="+1234567890",
            role="creator",
            preferences=Preferences(
                vibe=["culture"],
                interests=["food", "museums"],
                departure_airports=["LAX"],
                budget=Budget(min=1800, max=2800),
                trip_duration=7,
                travel_style="balanced",
                pace="balanced"
            ),
            availability=Availability(dates=["2024-06-15", "2024-06-16"])
        )
        
        user2 = UserInput(
            name="Bob Johnson",
            email="bob@example.com",
            phone="+1234567890",
            role="member",
            preferences=Preferences(
                vibe=["culture", "adventurous"],
                interests=["culture", "art"],
                departure_airports=["SFO"],
                budget=Budget(min=1500, max=2500),
                trip_duration=7,
                travel_style="balanced",
                pace="balanced"
            ),
            availability=Availability(dates=["2024-06-15", "2024-06-16"])
        )
        
        # Add users to group
        storage.add_user_to_group(user1, "INTEGRATION_TEST")
        storage.add_user_to_group(user2, "INTEGRATION_TEST")
        
        # Step 3: Verify group data
        group_data = storage.get_group_data("INTEGRATION_TEST")
        assert len(group_data) == 2
        assert group_data[0].email == "alice@example.com"
        assert group_data[1].email == "bob@example.com"
        
        # Step 4: Get aggregated preferences
        preferences = get_group_preferences(group_data)
        assert "interests" in preferences
        assert "food" in preferences["interests"]
        assert "culture" in preferences["interests"]
        assert "museums" in preferences["interests"]
        assert "art" in preferences["interests"]
        
        # Step 5: Mock trip planning
        with patch('app.services.planner.travel_agent') as mock_agent:
            mock_agent.plan_trip.return_value = {
                "success": True,
                "destinations": ["Barcelona", "Paris"],
                "itinerary": "7-day Barcelona and Paris itinerary",
                "estimated_cost": 2200,
                "flights": {"LAX": {"price": 650}, "SFO": {"price": 700}},
                "hotels": {"Barcelona": {"price": 150}, "Paris": {"price": 200}}
            }
            
            # Test planning
            result = await plan_trip("INTEGRATION_TEST")
            
            # Verify results
            assert result is not None
            assert "destinations" in result
            assert len(result["destinations"]) == 2
            assert "Barcelona" in result["destinations"]
            assert "Paris" in result["destinations"]


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 