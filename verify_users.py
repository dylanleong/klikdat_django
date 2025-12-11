import requests
import sys

BASE_URL = "http://localhost:8000/api"

def verify_users_endpoint():
    # 1. Register/Login to get token
    email = "testuser_unique@example.com"
    username = "testuser_unique"
    password = "password123"
    
    # Try logging in first
    login_data = {
        "username": username,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
    
    if response.status_code != 200:
        print("Login failed, trying to register...")
        # Register if login fails
        register_data = {
            "username": username,
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User"
        }
        response = requests.post(f"{BASE_URL}/auth/register/", data=register_data)
        if response.status_code != 201:
             # Maybe already exists but password wrong?
             print(f"Registration failed: {response.text}")
             if "already exists" in response.text:
                 print("User likely exists, check credentials or manual cleanup needed.")
             return False

        # Login again after registration
        response = requests.post(f"{BASE_URL}/auth/login/", data=login_data)
        if response.status_code != 200:
            print(f"Login after register failed: {response.text}")
            return False

    tokens = response.json()
    access_token = tokens["access"]
    print("Obtained access token.")

    # 2. List users
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/users/", headers=headers)
    
    if response.status_code == 200:
        print("Successfully listed users:")
        print(response.json())
        return True
    else:
        print(f"Failed to list users: {response.status_code} {response.text}")
        return False

if __name__ == "__main__":
    if verify_users_endpoint():
        print("Verification SUCCESS")
    else:
        print("Verification FAILED")
        sys.exit(1)
