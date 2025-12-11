
import os
import django
from django.core.exceptions import ValidationError

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleType, Make, Model

def verify_model_validation():
    print("Verifying Vehicle Model Validation (Admin Enforcement)...")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='test_admin_user')
    car_type, _ = VehicleType.objects.get_or_create(vehicle_type="Car")
    
    make1, _ = Make.objects.get_or_create(make="Make1")
    make1.vehicle_types.add(car_type)
    
    make2, _ = Make.objects.get_or_create(make="Make2")
    make2.vehicle_types.add(car_type)
    
    # Model1 belongs to Make1
    model1, _ = Model.objects.get_or_create(model="Model1", make=make1, defaults={'vehicle_type': car_type})
    
    print(f"Created Data: Make1={make1}, Make2={make2}, Model1={model1} (linked to Make1)")
    
    # 2. Try to instantiate Vehicle with Mismatched Make/Model
    # Note: Model validation (clean) is NOT called on .save() by default, 
    # but IS called by Admin forms. We simulate strict checking by calling full_clean().
    
    vehicle = Vehicle(
        owner=user,
        vehicle_type=car_type,
        make=make2,  # Mismatch! Model1 linked to Make1
        model=model1,
        year=2022,
        price=10000,
        location='Test Location',
        mileage=500,
        specifications={}
    )
    
    print("\nAttempting vehicle.full_clean() with Mismatched Make/Model...")
    try:
        vehicle.full_clean()
        print("FAIL: Validation passed (it should have failed).")
    except ValidationError as e:
        print(f"PASS: Validation failed as expected: {e.message_dict}")
    except Exception as e:
        print(f"FAIL: Unexpected error: {e}")

if __name__ == '__main__':
    verify_model_validation()
