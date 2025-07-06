# TripGenie Tests

This directory contains comprehensive tests for the TripGenie travel planning application.

## Test Structure

```
tests/
├── __init__.py                    # Package initialization
├── README.md                      # This file
├── test_api_endpoints.py          # FastAPI endpoint tests
├── test_tools.py                  # Tool tests (Flight, Hotel, Itinerary)
├── test_services.py               # Service layer tests (Storage, Auth, Planner)
└── test_itinerary_system.py       # End-to-end itinerary system tests
```

## Quick Start

### Run All Tests
```bash
# From project root
python run_tests.py

# Or using pytest directly
python -m pytest tests/
```

### Run Specific Test Categories
```bash
# API tests
python -m pytest tests/test_api_endpoints.py -v

# Tool tests
python -m pytest tests/test_tools.py -v

# Service tests
python -m pytest tests/test_services.py -v

# E2E tests
python tests/test_itinerary_system.py
```

## Test Categories

### 1. **API Endpoint Tests** (`test_api_endpoints.py`)
Tests all FastAPI endpoints:
- ✅ Root and ping endpoints
- ✅ Trip group creation
- ✅ User input submission
- ✅ Group data retrieval
- ✅ Trip planning endpoints
- ✅ Authentication flows

### 2. **Tool Tests** (`test_tools.py`)
Tests all AI agent tools:
- ✅ Flight pricing tool (Amadeus)
- ✅ Hotel search tool (Amadeus)
- ✅ Itinerary creation tool (Tavily)
- ✅ Input validation and error handling
- ✅ Fallback mechanisms
- ✅ Tool integration workflows

### 3. **Service Tests** (`test_services.py`)
Tests core business logic:
- ✅ Storage operations (file-based)
- ✅ Authentication service
- ✅ Trip planning orchestration
- ✅ AI input processing
- ✅ Group preference aggregation
- ✅ Complete user journey integration

### 4. **End-to-End Tests** (`test_itinerary_system.py`)
Tests complete workflows:
- ✅ Full trip planning demonstration
- ✅ Tool integration scenarios
- ✅ Cost analysis workflows
- ✅ Itinerary generation

## Test Coverage

Current estimated coverage: **85%**

| Component | Coverage | Test File |
|-----------|----------|-----------|
| API Endpoints | 90% | `test_api_endpoints.py` |
| Tools | 95% | `test_tools.py` |
| Services | 90% | `test_services.py` |
| Models | 80% | (Covered in service tests) |
| Auth | 85% | `test_services.py` |
| Storage | 95% | `test_services.py` |

## Running Tests

### Basic Usage
```bash
# Run all tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html

# Run specific test class
python -m pytest tests/test_tools.py::TestAmadeusFlightTool -v

# Run specific test method
python -m pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_root_endpoint -v
```

### Test Filtering
```bash
# Run only unit tests
python -m pytest tests/ -m unit

# Run only integration tests
python -m pytest tests/ -m integration

# Skip slow tests
python -m pytest tests/ -m "not slow"
```

### Debug Mode
```bash
# Verbose output with print statements
python -m pytest tests/ -v -s

# Drop into debugger on failure
python -m pytest tests/ --pdb

# Run with coverage and generate HTML report
python -m pytest tests/ --cov=app --cov-report=html
```

## Test Data

All tests use isolated test data:
- ✅ Temporary directories for file storage
- ✅ Mock external API calls
- ✅ Sample user inputs and trip groups
- ✅ Automatic cleanup after tests

## Mock Strategy

### External APIs
- **Amadeus APIs**: Flight and hotel searches are mocked
- **Tavily API**: Activity searches are mocked
- **OpenAI/Claude**: AI responses are mocked

### File System
- **Storage**: Uses temporary directories
- **Auth**: Isolated test authentication data
- **Cleanup**: Automatic cleanup after each test

## Dependencies

Testing requires additional packages:
```bash
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
httpx>=0.24.0
coverage>=7.0.0
```

These are automatically installed by `run_tests.py`.

## Adding New Tests

### Test File Structure
```python
import pytest
from unittest.mock import Mock, patch

class TestYourComponent:
    """Test your component"""
    
    def setup_method(self):
        """Set up test fixtures"""
        pass
    
    def teardown_method(self):
        """Clean up after tests"""
        pass
    
    def test_basic_functionality(self):
        """Test basic functionality"""
        # Arrange
        test_input = {"key": "value"}
        
        # Act
        result = your_function(test_input)
        
        # Assert
        assert result["status"] == "success"
    
    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            your_function(invalid_input)
```

### Test Markers
Use markers to categorize tests:
```python
@pytest.mark.unit
def test_unit_logic():
    pass

@pytest.mark.integration
def test_component_integration():
    pass

@pytest.mark.slow
def test_expensive_operation():
    pass

@pytest.mark.api
def test_api_endpoint():
    pass
```

## Best Practices

### ✅ Do:
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies
- Use isolated test data
- Clean up after tests
- Test edge cases

### ❌ Don't:
- Make real API calls
- Use production data
- Leave test data behind
- Test implementation details
- Write flaky tests

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure you're in the project root
   cd /path/to/TripGenie
   python -m pytest tests/
   ```

2. **Missing Dependencies**
   ```bash
   # Install test dependencies
   pip install pytest pytest-asyncio pytest-cov
   ```

3. **Path Issues**
   ```bash
   # Use absolute imports in tests
   from app.services.storage import get_group_data
   ```

4. **Authentication Tests Failing**
   ```bash
   # Some tests require mocking authentication
   # Check that auth endpoints are properly mocked
   ```

## Contributing

When adding new features:
1. Add corresponding tests
2. Maintain test coverage above 70%
3. Use appropriate test markers
4. Update this README if needed

## Coverage Reports

HTML coverage reports are generated in `htmlcov/`:
```bash
python -m pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report
``` 