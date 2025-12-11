
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleType, Make, Model

def verify_new_fields():
    print("Verifying Tax and Boot Space Fields...")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='test_field_user')
    car_type, _ = VehicleType.objects.get_or_create(vehicle_type="Car")
    make, _ = Make.objects.get_or_create(make="TestMake")
    make.vehicle_types.add(car_type)
    model, _ = Model.objects.get_or_create(model="TestModel", make=make, defaults={'vehicle_type': car_type})
    
    # ensure clean slate
    Vehicle.objects.filter(owner=user).delete()
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    data = {
        'vehicle_type': car_type.id,
        'make': make.id,
        'model': model.id,
        'year': 2023,
        'price': 25000,
        'location': 'Test Location',
        'mileage': 5000,
        'tax_per_year': 150.50,
        'boot_space': 450,
        'specifications': {}
    }
    
    print("\nAttempting to create vehicle with new fields...")
    response = client.post('/api/vehicles/', data, format='json')
    
    if response.status_code == 201:
        vehicle = Vehicle.objects.get(id=response.data['id'])
        print("PASS: Vehicle created successfully.")
        
        # Verify fields in DB
        db_tax = float(vehicle.tax_per_year) if vehicle.tax_per_year else None
        db_boot = vehicle.boot_space
        
        if db_tax == 150.50 and db_boot == 450:
             print(f"PASS: DB Values correct. Tax={db_tax}, Boot={db_boot}")
        else:
             print(f"FAIL: DB Values mismatch. Tax={db_tax}, Boot={db_boot}")

        # Verify fields in API response
        api_tax = response.data.get('tax_per_year')
        api_boot = response.data.get('boot_space')
         
        # DRF returns Decimal as string usually
        if float(api_tax) == 150.50 and api_boot == 450:
             print(f"PASS: API Values correct. Tax={api_tax}, Boot={api_boot}")
        else:
             print(f"FAIL: API Values mismatch. Tax={api_tax}, Boot={api_boot}")

        # Cleanup
        vehicle.delete()
    else:
        print(f"FAIL: Vehicle creation failed. Status: {response.status_code}")
        print(response.data)

if __name__ == '__main__':
    verify_new_fields()
