
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleType, Make, Model

def verify_make_model_dependency():
    print("Verifying Make-Model Dependency Enforcement...")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='test_dep_user')
    
    car_type, _ = VehicleType.objects.get_or_create(vehicle_type="Car")
    
    make1, _ = Make.objects.get_or_create(make="Make1")
    make1.vehicle_types.add(car_type)
    
    make2, _ = Make.objects.get_or_create(make="Make2")
    make2.vehicle_types.add(car_type)
    
    # Model1 belongs to Make1
    model1, _ = Model.objects.get_or_create(model="Model1", make=make1, defaults={'vehicle_type': car_type})
    
    print(f"Created Data: Make1={make1.id}, Make2={make2.id}, Model1={model1.id} (linked to Make1)")
    
    # 2. Try to create Vehicle with Mismatched Make/Model (Make2 + Model1)
    client = APIClient()
    client.force_authenticate(user=user)
    
    data = {
        'vehicle_type': car_type.id,
        'make': make2.id,  # Mismatch! Model1 belongs to Make1
        'model': model1.id,
        'year': 2022,
        'price': 10000,
        'location': 'Test Location',
        'mileage': 1000,
        'specifications': {}
    }
    
    print("\nAttempting to create mismatched vehicle (Make2 + Model1)...")
    response = client.post('/api/vehicles/', data, format='json')
    
    if response.status_code == 201:
        print("FAIL: Mismatched vehicle created successfully.")
        print(f"Vehicle ID: {response.data['id']}")
        # Cleanup
        Vehicle.objects.get(id=response.data['id']).delete()
    else:
        print(f"PASS: Mismatched vehicle creation failed. Status: {response.status_code}")
        print(response.data)

if __name__ == '__main__':
    verify_make_model_dependency()
