
import os
import django
import sys

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from rest_framework.test import APIClient
from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleProfile, SellerType, VehicleType, Make, Model

def verify_vehicle_profile():
    print("Verifying Vehicle Profile Logic...")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='test_profile_user')
    user.set_password('password')
    user.save()
    
    # Ensure no existing profile
    VehicleProfile.objects.filter(user=user).delete()
    
    # Ensure 'Private' and 'Dealer' SellerTypes exist
    private_type, _ = SellerType.objects.get_or_create(seller_type='Private')
    dealer_type, _ = SellerType.objects.get_or_create(seller_type='Dealer')
    
    car_type, _ = VehicleType.objects.get_or_create(vehicle_type="Car")
    make, _ = Make.objects.get_or_create(make="TestMake")
    model, _ = Model.objects.get_or_create(model="TestModel", make=make, defaults={'vehicle_type': car_type})
    
    # 2. Test Auto-Creation on Vehicle Create
    print("\nTesting Auto-Creation of Profile...")
    client = APIClient()
    client.force_authenticate(user=user)
    
    data = {
        'vehicle_type': car_type.id,
        'make': make.id,
        'model': model.id,
        'year': 2022,
        'price': 10000,
        'location': 'Test Location',
        'mileage': 50000,
        'specifications': {}
    }
    
    response = client.post('/api/vehicles/', data, format='json')
    if response.status_code == 201:
        print("PASS: Vehicle created successfully.")
        vehicle_id = response.data['id']
        vehicle = Vehicle.objects.get(id=vehicle_id)
        
        # Check Seller Type
        if vehicle.seller_type == private_type:
            print("PASS: Vehicle has 'Private' seller type.")
        else:
            print(f"FAIL: Vehicle seller type is {vehicle.seller_type}, expected Private.")
            
        # Check Profile Creation
        if VehicleProfile.objects.filter(user=user).exists():
            profile = VehicleProfile.objects.get(user=user)
            print("PASS: VehicleProfile created.")
            if profile.seller_type == private_type:
                print("PASS: Profile has 'Private' seller type.")
            else:
                print(f"FAIL: Profile seller type is {profile.seller_type}.")
        else:
            print("FAIL: VehicleProfile not created.")
            
    else:
        print(f"FAIL: Vehicle creation failed: {response.data}")
        
    # 3. Test Profile Update and subsequent Vehicle Create
    print("\nTesting Profile Update Influence...")
    # Update profile to Dealer
    profile = VehicleProfile.objects.get(user=user)
    profile.seller_type = dealer_type
    profile.save()
    print("Updated profile to 'Dealer'.")
    
    # Create another vehicle
    response2 = client.post('/api/vehicles/', data, format='json')
    if response2.status_code == 201:
        vehicle2_id = response2.data['id']
        vehicle2 = Vehicle.objects.get(id=vehicle2_id)
        
        if vehicle2.seller_type == dealer_type:
            print("PASS: Second vehicle has 'Dealer' seller type.")
        else:
            print(f"FAIL: Second vehicle seller type is {vehicle2.seller_type}, expected Dealer.")
    else:
         print(f"FAIL: Second vehicle creation failed: {response2.data}")

    # Cleanup
    # user.delete() # keeping for inspection if needed

if __name__ == '__main__':
    verify_vehicle_profile()
