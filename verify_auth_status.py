import os
import django
import sys
import json

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.contrib.auth.models import User
from rest_framework.test import APIRequestFactory, force_authenticate
from accounts.views import AuthStatusView

def run():
    print("--- Testing Auth Status Endpoint ---")
    
    # Create or get superuser
    username = 'debug_superuser'
    email = 'debug@example.com'
    password = 'password123'
    
    user, created = User.objects.get_or_create(username=username, email=email)
    if created:
        user.set_password(password)
        user.is_superuser = True
        user.is_staff = True
        user.save()
        print(f"Created superuser: {username}")
    else:
        # Ensure it is superuser
        if not user.is_superuser:
            user.is_superuser = True
            user.save()
            print(f"Updated existing user {username} to superuser.")
        else:
            print(f"Using existing superuser: {username}")
            
    # Test View
    factory = APIRequestFactory()
    request = factory.get('/api/accounts/status/')
    force_authenticate(request, user=user)
    
    view = AuthStatusView.as_view()
    response = view(request)
    
    print(f"Response Status: {response.status_code}")
    print("Response Data:")
    print(json.dumps(response.data, indent=2))
    
    if 'is_superuser' in response.data:
        print(f"SUCCESS: is_superuser found (Value: {response.data['is_superuser']})")
    else:
        print("FAILURE: is_superuser missing from response.")

if __name__ == '__main__':
    run()
