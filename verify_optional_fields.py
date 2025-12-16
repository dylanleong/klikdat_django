import os
import django
import sys
import json

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleType, Make, Model, SellerType

def run():
    print("--- Testing Optional Vehicle Fields ---")
    
    # Setup data
    user, _ = User.objects.get_or_create(username='test_optional_fields', email='optional@test.com')
    vt, _ = VehicleType.objects.get_or_create(vehicle_type='Car')
    make, _ = Make.objects.get_or_create(make='TestMake')
    make.vehicle_types.add(vt)
    model, _ = Model.objects.get_or_create(model='TestModel', make=make, vehicle_type=vt)
    seller_type, _ = SellerType.objects.get_or_create(seller_type='Private')
    
    # Try creating vehicle without optional fields
    print("Attempting to create vehicle WITHOUT price, year, mileage, location...")
    
    try:
        vehicle = Vehicle.objects.create(
            owner=user,
            vehicle_type=vt,
            make=make,
            model=model,
            seller_type=seller_type,
            # NOT providing price, year, mileage, location
        )
        print(f"SUCCESS: Created vehicle ID {vehicle.id}")
        print(f"Fields - Price: {vehicle.price}, Year: {vehicle.year}, Mileage: {vehicle.mileage}, Location: {vehicle.location}")
        
    except Exception as e:
        print(f"FAILURE: Could not create vehicle. Error: {e}")

if __name__ == '__main__':
    run()
