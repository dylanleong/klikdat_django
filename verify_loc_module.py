
import requests
import json
import os

# Configuration
BASE_URL = "http://localhost:8000"
USERNAME = "testuser_loc"
PASSWORD = "password123"
EMAIL = "test_loc@example.com"

def run_verification():
    print("Starting Location Module Verification...")

    # 1. Create/Register User (if not exists) or Login
    print("\n[1] Authenticating...")
    login_url = f"{BASE_URL}/api/auth/login/"
    response = requests.post(login_url, data={'username': USERNAME, 'password': PASSWORD})
    
    if response.status_code != 200:
        print("User might not exist, trying to register...")
        # Usually user registration endpoint might allow creating user
        # But for simplicity, let's assume valid user or create via django shell if needed.
        # Let's try to register if auth fails
        register_url = f"{BASE_URL}/api/auth/register/" 
        # CAUTION: Adjust according to actual register implementation
        reg_data = {
            "username": USERNAME,
            "password": PASSWORD,
            "email": EMAIL,
            "first_name": "Test",
            "last_name": "Loc"
        }
        reg_resp = requests.post(register_url, data=reg_data)
        if reg_resp.status_code in [200, 201]:
             print("Registered successfully. Logging in...")
             response = requests.post(login_url, data={'username': USERNAME, 'password': PASSWORD})
        else:
            print(f"Registration failed: {reg_resp.text}")
            return

    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return

    tokens = response.json()
    access_token = tokens['access']
    headers = {"Authorization": f"Bearer {access_token}"}
    print("Authentication successful.")

    # 2. Post a Location
    print("\n[2] Posting a location...")
    loc_data = {
        "latitude": "37.774900",
        "longitude": "-122.419400",
        "device_id": "device_123"
    }
    
    # Note: Using locations/locations because we registered router(r'locations', ...) 
    # and included it under api/locations/ so it usually results in api/locations/locations/
    # Wait, in urls.py: path('api/locations/', include('locations.urls'))
    # In locations/urls.py: router.register(r'locations', LocationViewSet)
    # So the URL is /api/locations/locations/
    
    post_url = f"{BASE_URL}/api/locations/locations/"
    resp = requests.post(post_url, data=loc_data, headers=headers)
    
    if resp.status_code == 201:
        print("Location posted successfully.")
        location_id = resp.json()['id']
        print(f"Location ID: {location_id}")
    else:
        print(f"Failed to post location: {resp.status_code} {resp.text}")
        return

    # 3. List Locations
    print("\n[3] Listing locations...")
    resp = requests.get(post_url, headers=headers)
    if resp.status_code == 200:
        results = resp.json()
        print(f"Found {len(results)} locations.")
        # Verify our location is in the list
        if 'results' in results:
            item_list = results['results']
        else:
            item_list = results
        
        found = any(loc['id'] == location_id for loc in item_list)
        if found:
            print("Verified: Posted location found in list.")
        else:
            print("Error: Posted location NOT found in list.")
    else:
         print(f"Failed to list locations: {resp.status_code} {resp.text}")

    # 4. Delete Location
    print("\n[4] Deleting location...")
    # Clean up
    del_url = f"{post_url}{location_id}/"
    resp = requests.delete(del_url, headers=headers)
    if resp.status_code == 204:
        print("Location deleted successfully.")
    else:
        print(f"Failed to delete location: {resp.status_code} {resp.text}")

    print("\nVerification Complete.")

if __name__ == "__main__":
    run_verification()
