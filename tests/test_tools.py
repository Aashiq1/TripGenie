import pytest
import json
from unittest.mock import Mock, patch, MagicMock
import os

# Mock environment variables before importing
os.environ.setdefault('AMADEUS_CLIENT_ID', 'test_client_id')
os.environ.setdefault('AMADEUS_CLIENT_SECRET', 'test_client_secret')
os.environ.setdefault('OPENAI_API_KEY', 'test_openai_key')
os.environ.setdefault('TAVILY_API_KEY', 'test_tavily_key')

from app.tools.amadeus_flight_tool import AmadeusFlightTool
from app.tools.amadeus_hotel_tool import HotelSearchTool
from app.tools.tavily_itinerary_tool import ItineraryTool

class TestAmadeusFlightTool:
    """Test the flight pricing tool"""
    
    def setup_method(self):
        self.tool = AmadeusFlightTool()
    
    def test_tool_initialization(self):
        """Test that tool initializes correctly"""
        assert self.tool.name == "flight_prices"
        assert "flight prices" in self.tool.description.lower()
    
    def test_valid_input_structure(self):
        """Test with valid input structure"""
        test_input = {
            "flight_groups": [
                {
                    "departure_city": "LAX",
                    "passenger_count": 2,
                    "destinations": ["BCN", "CDG"],
                    "departure_date": "2024-06-15",
                    "return_date": "2024-06-22"
                }
            ],
            "flight_preferences": {
                "travel_class": "economy",
                "nonstop_preferred": False
            }
        }
        
        # Mock the flight service to avoid API calls
        with patch('app.services.amadeus_flights.get_flight_offers') as mock_flight:
            mock_flight.return_value = {
                "price_round_trip": 650,
                "outbound_flight": "DL447",
                "return_flight": "DL448"
            }
            
            result = self.tool._call(json.dumps(test_input))
            result_data = json.loads(result)
            
            assert "LAX_x2" in result_data
            assert "BCN" in result_data["LAX_x2"]
            assert "CDG" in result_data["LAX_x2"]
    
    def test_invalid_json_input(self):
        """Test with invalid JSON input"""
        result = self.tool._call("invalid json")
        result_data = json.loads(result)
        assert "error" in result_data
    
    def test_backward_compatibility(self):
        """Test old input format still works"""
        old_format_input = {
            "departure_city": "LAX",
            "destinations": ["BCN"],
            "departure_date": "2024-06-15",
            "return_date": "2024-06-22"
        }
        
        with patch('app.services.amadeus_flights.get_flight_offers') as mock_flight:
            mock_flight.return_value = {"price_round_trip": 650}
            
            result = self.tool._call(json.dumps(old_format_input))
            result_data = json.loads(result)
            
            # Should convert to new format
            assert "LAX_x1" in result_data or "error" not in result_data


class TestHotelSearchTool:
    """Test the hotel search tool"""
    
    def setup_method(self):
        self.tool = HotelSearchTool()
    
    def test_tool_initialization(self):
        """Test that tool initializes correctly"""
        assert self.tool.name == "hotel_search"
        assert "hotel" in self.tool.description.lower()
    
    def test_valid_input_structure(self):
        """Test with valid input structure"""
        test_input = {
            "destinations": ["BCN"],
            "check_in": "2024-06-15",
            "check_out": "2024-06-22",
            "group_accommodation_style": "standard",
            "accommodation_details": [
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "room_sharing": "any"
                },
                {
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "room_sharing": "any"
                }
            ]
        }

        # Mock all the hotel service functions
        with patch('app.services.amadeus_hotels.get_hotel_offers') as mock_hotel, \
             patch('app.services.amadeus_hotels.assign_rooms_smartly') as mock_assign, \
             patch('app.services.amadeus_hotels.calculate_total_accommodation_cost') as mock_calc:
            
            # Mock hotel search returns empty (triggers fallback)
            mock_hotel.return_value = []
            
            # Mock room assignment
            mock_assign.return_value = {
                'summary': '1 double room',
                'total_cost_per_night': 150
            }
            
            # Mock cost calculation
            mock_calc.return_value = {
                'total_group_cost': 1050,
                'individual_costs': {
                    'john@example.com': {
                        'name': 'John Doe',
                        'email': 'john@example.com',
                        'room_type': 'double',
                        'cost_per_night': 75,
                        'total_cost': 525,
                        'sharing_with': ['Jane Smith']
                    },
                    'jane@example.com': {
                        'name': 'Jane Smith',
                        'email': 'jane@example.com',
                        'room_type': 'double',
                        'cost_per_night': 75,
                        'total_cost': 525,
                        'sharing_with': ['John Doe']
                    }
                }
            }

            result = self.tool._call(json.dumps(test_input))
            result_data = json.loads(result)

            assert "BCN" in result_data
            assert "hotels" in result_data["BCN"]
            assert len(result_data["BCN"]["hotels"]) > 0
    
    def test_fallback_estimation(self):
        """Test fallback when API fails"""
        test_input = {
            "destinations": ["BCN"],
            "check_in": "2024-06-15",
            "check_out": "2024-06-22",
            "group_accommodation_style": "standard",
            "accommodation_details": [
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "room_sharing": "any"
                }
            ]
        }
        
        # Mock API to return empty results (triggers fallback)
        with patch('app.services.amadeus_hotels.get_hotel_offers') as mock_hotel:
            mock_hotel.return_value = []
            
            result = self.tool._call(json.dumps(test_input))
            result_data = json.loads(result)
            
            assert "BCN" in result_data
            assert "hotels" in result_data["BCN"]
            # Should have fallback estimates
            hotel = result_data["BCN"]["hotels"][0]
            assert "Estimated" in hotel["hotel_name"]
    
    def test_invalid_json_input(self):
        """Test with invalid JSON input"""
        result = self.tool._call("invalid json")
        result_data = json.loads(result)
        assert "error" in result_data


class TestItineraryTool:
    """Test the itinerary creation tool"""
    
    def setup_method(self):
        self.tool = ItineraryTool()
    
    def test_tool_initialization(self):
        """Test that tool initializes correctly"""
        assert self.tool.name == "itinerary_generator"
        assert "itinerary" in self.tool.description.lower() or "itineraries" in self.tool.description.lower()
    
    def test_valid_input_structure(self):
        """Test with valid input structure"""
        test_input = {
            "destination": "Barcelona",
            "interests": ["food", "culture", "museums"],
            "travel_style": "standard",
            "num_days": 5,
            "trip_pace": "balanced"
        }
        
        # Mock the activity service to avoid API calls
        with patch.object(self.tool, 'activity_service') as mock_service:
            mock_service.search_activities.return_value = {
                "activities": [
                    {
                        "name": "Sagrada Familia",
                        "duration": 2.5,
                        "cost": 25,
                        "category": "culture"
                    }
                ],
                "total_activities": 1
            }
            
            result = self.tool._call(json.dumps(test_input))
            result_data = json.loads(result)
            
            assert "daily_itinerary" in result_data
            assert "summary" in result_data
            assert result_data["summary"]["destination"] == "Barcelona"
    
    def test_fallback_itinerary(self):
        """Test fallback when search fails"""
        test_input = {
            "destination": "Barcelona",
            "interests": ["food", "culture"],
            "travel_style": "standard",
            "num_days": 3,
            "trip_pace": "balanced"
        }
        
        # Mock service to raise exception (triggers fallback)
        with patch.object(self.tool, 'activity_service') as mock_service:
            mock_service.search_activities.side_effect = Exception("API Error")
            
            result = self.tool._call(json.dumps(test_input))
            result_data = json.loads(result)
            
            assert "fallback_itinerary" in result_data
            assert "error" in result_data
    
    def test_invalid_json_input(self):
        """Test with invalid JSON input"""
        result = self.tool._call("invalid json")
        result_data = json.loads(result)
        assert "error" in result_data
    
    def test_missing_destination(self):
        """Test with missing required destination"""
        test_input = {
            "interests": ["food", "culture"],
            "travel_style": "standard",
            "num_days": 5
        }
        
        result = self.tool._call(json.dumps(test_input))
        result_data = json.loads(result)
        
        assert "error" in result_data
        assert "required" in result_data["error"].lower()


# Integration test for all tools working together
class TestToolIntegration:
    """Test tools working together in a realistic scenario"""
    
    def test_complete_trip_planning_workflow(self):
        """Test a complete trip planning workflow using all tools"""
        # Sample group data
        flight_input = {
            "flight_groups": [
                {
                    "departure_city": "LAX",
                    "passenger_count": 2,
                    "destinations": ["BCN"],
                    "departure_date": "2024-06-15",
                    "return_date": "2024-06-22"
                }
            ]
        }
        
        hotel_input = {
            "destinations": ["BCN"],
            "check_in": "2024-06-15",
            "check_out": "2024-06-22",
            "group_accommodation_style": "standard",
            "accommodation_details": [
                {"name": "John", "email": "john@example.com", "room_sharing": "any"},
                {"name": "Jane", "email": "jane@example.com", "room_sharing": "any"}
            ]
        }
        
        itinerary_input = {
            "destination": "Barcelona",
            "interests": ["food", "culture"],
            "travel_style": "standard",
            "num_days": 7,
            "trip_pace": "balanced"
        }
        
        # Initialize tools
        flight_tool = AmadeusFlightTool()
        hotel_tool = HotelSearchTool()
        itinerary_tool = ItineraryTool()
        
        # Mock external services
        with patch('app.services.amadeus_flights.get_flight_offers') as mock_flight, \
             patch('app.services.amadeus_hotels.get_hotel_offers') as mock_hotel, \
             patch.object(itinerary_tool, 'activity_service') as mock_activity:
            
            # Mock responses
            mock_flight.return_value = {"price_round_trip": 650}
            mock_hotel.return_value = []  # Will use fallback
            mock_activity.search_activities.return_value = {
                "activities": [{"name": "Test Activity", "duration": 2, "cost": 20}],
                "total_activities": 1
            }
            
            # Execute all tools
            flight_result = flight_tool._call(json.dumps(flight_input))
            hotel_result = hotel_tool._call(json.dumps(hotel_input))
            itinerary_result = itinerary_tool._call(json.dumps(itinerary_input))
            
            # Verify all tools returned valid results
            assert json.loads(flight_result)
            assert json.loads(hotel_result)
            assert json.loads(itinerary_result)
            
            # Verify no errors in responses
            flight_data = json.loads(flight_result)
            hotel_data = json.loads(hotel_result)
            itinerary_data = json.loads(itinerary_result)
            
            assert "error" not in flight_data
            assert "error" not in hotel_data
            # Itinerary might have error but should have fallback
            if "error" in itinerary_data:
                assert "fallback_itinerary" in itinerary_data


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 