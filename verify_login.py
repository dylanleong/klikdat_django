import os
import django
import sys
import json
import requests

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory

def run():
    print("--- Testing Login with Username and Email ---")
    
    username = 'login_test_user'
    email = 'login_test@example.com'
    password = 'password123'
    
    # Clean up existing user
    try:
        u = User.objects.get(username=username)
        u.delete()
    except User.DoesNotExist:
        pass
        
    # Create user
    user = User.objects.create_user(username=username, email=email, password=password)
    print(f"Created user: {username} ({email})")
    
    # Test Login with Username
    print("\nAttempting login with USERNAME...")
    # Since we are running outside of the server process via script, we can't easily hit the live URL 
    # unless we use requests against localhost:8000. 
    # But inside the container, localhost might refer to the container itself.
    # The server is running on port 8000 inside the container.
    
    url = 'http://localhost:8000/api/auth/login/'
    
    try:
        # 1. Login with Username
        data_username = {'username': username, 'password': password}
        response = requests.post(url, data=data_username)
        
        if response.status_code == 200 and 'access' in response.json():
            print("SUCCESS: Login with USERNAME worked.")
        else:
            print(f"FAILURE: Login with USERNAME failed. Status: {response.status_code}, Body: {response.text}")

        # 2. Login with Email
        print("\nAttempting login with EMAIL...")
        data_email = {'username': email, 'password': password} # SimpleJWT expects 'username' field even if value is email
        response = requests.post(url, data=data_email)
        
        if response.status_code == 200 and 'access' in response.json():
            print("SUCCESS: Login with EMAIL worked.")
        else:
            print(f"FAILURE: Login with EMAIL failed. Status: {response.status_code}, Body: {response.text}")
            
    except Exception as e:
        print(f"ERROR: Could not connect to API. Is the server running? {e}")

if __name__ == '__main__':
    run()
