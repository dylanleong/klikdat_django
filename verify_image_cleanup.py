import os
import django
import sys
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleType, Make, Model, SellerType, VehicleImage

def run():
    print("--- Testing Image Cleanup ---")
    
    # 1. Setup Data
    user, _ = User.objects.get_or_create(username='cleanup_test_user')
    vt, _ = VehicleType.objects.get_or_create(vehicle_type='Car')
    make, _ = Make.objects.get_or_create(make='TestMake', defaults={})
    make.vehicle_types.add(vt)
    model, _ = Model.objects.get_or_create(model='TestModel', make=make, defaults={'vehicle_type': vt})
    seller_type, _ = SellerType.objects.get_or_create(seller_type='Private')

    vehicle = Vehicle.objects.create(
        owner=user,
        vehicle_type=vt,
        make=make,
        model=model,
        seller_type=seller_type,
        price=100, year=2020, mileage=1000, location='Test'
    )
    
    # 2. Upload Image
    print("Creating vehicle with image...")
    image_content = b"fakeimagecontent"
    uploaded_image = SimpleUploadedFile(name='cleanup_test.jpg', content=image_content, content_type='image/jpeg')
    
    v_img = VehicleImage(vehicle=vehicle, image=uploaded_image)
    v_img.save()
    
    image_path = v_img.image.path
    print(f"Image saved at: {image_path}")
    
    if os.path.exists(image_path):
        print("Confirmed: File exists on disk.")
    else:
        print("ERROR: File was not created?")
        return

    # 3. Delete Vehicle
    print("Deleting vehicle...")
    vehicle.delete()
    
    # 4. Check if file exists
    if os.path.exists(image_path):
        print("FAILURE: File still persists after deletion.")
    else:
        print("SUCCESS: File was deleted.")

if __name__ == '__main__':
    run()
