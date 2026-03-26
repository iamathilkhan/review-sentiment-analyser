import requests
import json
import time

BASE_URL = "http://127.0.0.1:5000"

def test_auth():
    print("Testing Registration...")
    session = requests.Session()
    
    # Needs CSRF token to register/login? Since they are API endpoints but we added CSRF protection to forms...
    # Oh wait, Flask-WTF CSRFProtect applies to all POST endpoints by default if not excluded.
    # Let's get the CSRF token first. We can get it by hitting the GET /auth/register page and extracting it.
    
    response = session.get(f"{BASE_URL}/auth/register")
    if response.status_code != 200:
        print(f"Failed to get register page: {response.text}")
        return
        
    import re
    match = re.search(r'name="csrf_token" value="(.*?)"', response.text)
    if not match:
        print("Could not find CSRF token.")
        return
    csrf_token = match.group(1)
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": csrf_token
    }
    
    # 1. Register
    reg_data = {
        "name": "API Test User",
        "email": f"api_test_{int(time.time())}@example.com",
        "password": "password123",
        "role": "customer"
    }
    
    reg_response = session.post(f"{BASE_URL}/auth/register", json=reg_data, headers=headers)
    print("Registration Response:", reg_response.status_code, reg_response.text)
    
    if reg_response.status_code != 201:
        print("Registration failed.")
        return
        
    # 2. Logout
    logout_response = session.post(f"{BASE_URL}/auth/logout", headers=headers)
    print("Logout Response:", logout_response.status_code, logout_response.text)
    
    # 3. Login
    login_data = {
        "email": reg_data["email"],
        "password": "password123"
    }
    login_response = session.post(f"{BASE_URL}/auth/login", json=login_data, headers=headers)
    print("Login Response:", login_response.status_code, login_response.text)
    
    # 4. Get Profile
    profile_response = session.get(f"{BASE_URL}/auth/me")
    print("Profile Response:", profile_response.status_code, profile_response.text)

if __name__ == "__main__":
    test_auth()
