#!/usr/bin/env python3
"""
Security Testing Script - Validate authentication and rate limiting features
Run from backend directory: python tests/test_security.py
"""

import requests
import time
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
TEST_EMAIL = f"test_{int(time.time())}@example.com"
TEST_PASSWORD = "Password123"
TEST_NAME = "Security Test User"

class SecurityTester:
    def __init__(self, base_url=API_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []

    def log(self, test_name, status, message):
        """Log test result."""
        emoji = "✅" if status == "PASS" else "❌"
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {emoji} {test_name}: {message}")
        self.results.append({"test": test_name, "status": status, "message": message})

    def test_registration(self):
        """Test user registration with rate limiting."""
        print("\n📝 Testing Registration Endpoint...")

        # Test 1: Valid registration
        payload = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": TEST_NAME
        }
        response = self.session.post(f"{self.base_url}/users/register", json=payload)

        if response.status_code == 200:
            self.log("Registration", "PASS", f"User created: {TEST_EMAIL}")
        else:
            self.log("Registration", "FAIL", f"Status {response.status_code}: {response.text}")

        # Test 2: Duplicate registration
        response = self.session.post(f"{self.base_url}/users/register", json=payload)
        if response.status_code == 409:  # Conflict
            self.log("Duplicate Registration", "PASS", "Correctly rejected duplicate email")
        else:
            self.log("Duplicate Registration", "FAIL", f"Expected 409, got {response.status_code}")

    def test_login_rate_limiting(self):
        """Test login rate limiting after 5 failed attempts."""
        print("\n🔐 Testing Login Rate Limiting...")

        # Make 6 failed login attempts (5 allowed, 6th blocked)
        for attempt in range(1, 7):
            payload = {"email": TEST_EMAIL, "password": "WrongPassword"}
            response = self.session.post(f"{self.base_url}/users/login", json=payload)

            if attempt < 5:
                if response.status_code == 401:
                    self.log(f"Failed Login Attempt {attempt}", "PASS", "Rejected bad credentials")
                else:
                    self.log(f"Failed Login Attempt {attempt}", "FAIL", f"Unexpected status {response.status_code}")

            elif attempt == 5:
                if response.status_code == 401:
                    self.log("Failed Login Attempt 5", "PASS", "Rejected after 5 failed attempts")
                else:
                    self.log("Failed Login Attempt 5", "FAIL", f"Unexpected status {response.status_code}")

            elif attempt == 6:
                if response.status_code == 429:  # Too Many Requests
                    self.log("Rate Limit Enforcement", "PASS", f"Blocked 6th attempt with 429: {response.json()['detail']}")
                else:
                    self.log("Rate Limit Enforcement", "FAIL", f"Expected 429, got {response.status_code}")

            time.sleep(0.2)  # Small delay between attempts

    def test_successful_login(self):
        """Test successful login and token generation."""
        print("\n✅ Testing Successful Login...")

        # Wait before retrying to avoid rate limiting
        print("   ⏳ Waiting for rate limit to cool down (30 seconds)...")
        time.sleep(30)

        # Fresh session to reset rate limit
        self.session = requests.Session()

        # Register new user for clean login test
        test_email = f"clean_{int(time.time())}@example.com"
        register_payload = {
            "email": test_email,
            "password": TEST_PASSWORD,
            "full_name": "Clean Test"
        }
        self.session.post(f"{self.base_url}/users/register", json=register_payload)

        # Login
        login_payload = {"email": test_email, "password": TEST_PASSWORD}
        response = self.session.post(f"{self.base_url}/users/login", json=login_payload)

        if response.status_code == 200:
            data = response.json()
            if "access_token" in data and "refresh_token" in data:
                self.log("Successful Login", "PASS", f"Tokens generated for {test_email}")
                self.access_token = data["access_token"]
                self.refresh_token = data["refresh_token"]
                self.test_email = test_email
                return True
        else:
            self.log("Successful Login", "FAIL", f"Status {response.status_code}: {response.text}")
            return False

        return False

    def test_authentication(self):
        """Test protected endpoint with JWT."""
        print("\n🔒 Testing Authentication...")

        if not hasattr(self, 'access_token'):
            self.log("Profile Access", "FAIL", "No access token from login")
            return

        # Test with cookie (default)
        response = self.session.get(f"{self.base_url}/users/profile")

        if response.status_code == 200:
            self.log("Profile Access (Cookie)", "PASS", "Successfully accessed protected endpoint")
        else:
            self.log("Profile Access (Cookie)", "FAIL", f"Status {response.status_code}")

        # Test with header
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = requests.get(f"{self.base_url}/users/profile", headers=headers)

        if response.status_code == 200:
            self.log("Profile Access (Header)", "PASS", "Authentication works with Bearer token")
        else:
            self.log("Profile Access (Header)", "FAIL", f"Status {response.status_code}")

    def test_token_refresh(self):
        """Test token refresh functionality."""
        print("\n🔄 Testing Token Refresh...")

        if not hasattr(self, 'refresh_token'):
            self.log("Token Refresh", "FAIL", "No refresh token available")
            return

        response = self.session.post(f"{self.base_url}/users/refresh")

        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                self.log("Token Refresh", "PASS", "Successfully generated new access token")
                self.access_token = data["access_token"]
            else:
                self.log("Token Refresh", "FAIL", "No access token in response")
        else:
            self.log("Token Refresh", "FAIL", f"Status {response.status_code}: {response.json()}")

    def test_logout(self):
        """Test logout and token blacklist."""
        print("\n🚪 Testing Logout...")

        response = self.session.post(f"{self.base_url}/users/logout")

        if response.status_code == 200:
            self.log("Logout", "PASS", "Successfully logged out")

            # Try to access protected endpoint - should fail
            time.sleep(0.5)
            response = self.session.get(f"{self.base_url}/users/profile")

            if response.status_code == 401:
                self.log("Token Blacklist", "PASS", "Token correctly invalidated after logout")
            else:
                self.log("Token Blacklist", "FAIL", f"Expected 401 after logout, got {response.status_code}")
        else:
            self.log("Logout", "FAIL", f"Status {response.status_code}")

    def test_health_check(self):
        """Test public health endpoint."""
        print("\n💚 Testing Health Check...")

        response = requests.get(f"{self.base_url}/health")

        if response.status_code == 200:
            data = response.json()
            if "status" in data and data["status"] == "healthy":
                self.log("Health Check", "PASS", f"API healthy - Environment: {data.get('environment', 'unknown')}")
            else:
                self.log("Health Check", "FAIL", "Unexpected response format")
        else:
            self.log("Health Check", "FAIL", f"Status {response.status_code}")

    def summary(self):
        """Print test summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)

        passed = sum(1 for r in self.results if r["status"] == "PASS")
        failed = sum(1 for r in self.results if r["status"] == "FAIL")
        total = len(self.results)

        for result in self.results:
            emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"{emoji} {result['test']}: {result['message']}")

        print("\n" + "-"*60)
        print(f"Results: {passed}/{total} passed, {failed} failed")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        print("="*60)

    def run_all(self):
        """Run all security tests."""
        print("\n" + "="*60)
        print("🔐 SECURITY TEST SUITE")
        print("="*60)
        print(f"API URL: {self.base_url}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        # Check if API is available
        try:
            self.test_health_check()
        except Exception as e:
            print(f"❌ Cannot connect to API: {e}")
            return

        try:
            self.test_registration()
            self.test_login_rate_limiting()

            if self.test_successful_login():
                self.test_authentication()
                self.test_token_refresh()
                self.test_logout()

            self.summary()

        except Exception as e:
            print(f"❌ Test execution error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    tester = SecurityTester()
    tester.run_all()
