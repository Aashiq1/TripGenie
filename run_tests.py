#!/usr/bin/env python3
"""
TripGenie Test Runner
Comprehensive testing script for the TripGenie travel planning application
"""

import os
import sys
import subprocess
import json
from datetime import datetime

def install_test_dependencies():
    """Install required testing dependencies"""
    print("📦 Installing test dependencies...")
    
    required_packages = [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "pytest-cov>=4.0.0",
        "pytest-mock>=3.10.0",
        "httpx>=0.24.0",  # For FastAPI testing
        "coverage>=7.0.0"
    ]
    
    for package in required_packages:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ Installed {package}")
        except subprocess.CalledProcessError:
            print(f"❌ Failed to install {package}")
            return False
    
    return True

def run_test_suite(test_file, description):
    """Run a specific test suite"""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return False
    
    try:
        # Run tests with verbose output and coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            test_file, 
            "-v", 
            "--tb=short",
            f"--cov=app",
            "--cov-report=term-missing"
        ], capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - All tests passed!")
            return True
        else:
            print(f"❌ {description} - Some tests failed")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Tests timed out")
        return False
    except Exception as e:
        print(f"❌ {description} - Error running tests: {e}")
        return False

def run_manual_test(test_file, description):
    """Run a test that requires manual execution"""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    if not os.path.exists(test_file):
        print(f"❌ Test file {test_file} not found")
        return False
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, timeout=60)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - Completed successfully!")
            return True
        else:
            print(f"❌ {description} - Failed")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - Test timed out")
        return False
    except Exception as e:
        print(f"❌ {description} - Error: {e}")
        return False

def check_environment():
    """Check if the environment is set up correctly"""
    print("🔍 Checking environment setup...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python {python_version.major}.{python_version.minor} is too old. Need Python 3.8+")
        return False
    else:
        print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check if we're in the right directory
    if not os.path.exists("app"):
        print("❌ Not in TripGenie root directory (app/ folder not found)")
        return False
    else:
        print("✅ In TripGenie root directory")
    
    # Check for key files
    key_files = [
        "app/main.py",
        "app/services/planner.py",
        "app/tools/amadeus_flight_tool.py",
        "requirements.txt"
    ]
    
    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} not found")
            return False
    
    return True

def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n📊 Test Coverage Analysis...")
    print("=" * 60)
    
    # List all Python files in the app directory
    python_files = []
    for root, dirs, files in os.walk("app"):
        for file in files:
            if file.endswith(".py") and not file.startswith("__"):
                python_files.append(os.path.join(root, file))
    
    print(f"📁 Found {len(python_files)} Python files to potentially test:")
    
    testable_components = {
        "API Endpoints": ["app/api/inputs.py", "app/api/auth.py"],
        "Tools": ["app/tools/amadeus_flight_tool.py", "app/tools/amadeus_hotel_tool.py", "app/tools/tavily_itinerary_tool.py"],
        "Services": ["app/services/planner.py", "app/services/storage.py", "app/services/auth.py", "app/services/ai_input.py"],
        "Models": ["app/models/group_inputs.py", "app/models/auth.py"],
        "Core": ["app/main.py"]
    }
    
    for category, files in testable_components.items():
        print(f"\n{category}:")
        for file_path in files:
            if os.path.exists(file_path):
                print(f"  ✅ {file_path} - Testable")
            else:
                print(f"  ❌ {file_path} - Not found")

def main():
    """Main test runner function"""
    print("🚀 TripGenie Test Suite Runner")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check environment
    if not check_environment():
        print("\n❌ Environment check failed. Please fix the issues above.")
        return 1
    
    # Install dependencies
    if not install_test_dependencies():
        print("\n❌ Failed to install test dependencies.")
        return 1
    
    # Test results tracking
    test_results = {}
    
    # Run test suites
    test_suites = [
        ("tests/test_api_endpoints.py", "API Endpoints"),
        ("tests/test_tools.py", "Tools (Flight, Hotel, Itinerary)"),
        ("tests/test_services.py", "Services (Storage, Auth, Planner)"),
        ("tests/test_itinerary_system.py", "Existing Itinerary System")
    ]
    
    for test_file, description in test_suites:
        if os.path.exists(test_file):
            test_results[description] = run_test_suite(test_file, description)
        else:
            print(f"\n⚠️  {test_file} not found - skipping {description}")
            test_results[description] = False
    
    # Generate test report
    generate_test_report()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 FINAL TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for description, passed in test_results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {description}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your codebase is well-tested.")
        return 0
    else:
        print(f"⚠️  {total_tests - passed_tests} test suite(s) failed or skipped.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 