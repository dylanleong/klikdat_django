import os
import django
import sys
from io import BytesIO
from PIL import Image

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from vehicles.models import Vehicle, VehicleType, Make, Model, SellerType, VehicleImage

def create_large_image(width=3000, height=3000, color='red'):
    file_obj = BytesIO()
    image = Image.new("RGB", (width, height), color)
    image.save(file_obj, format="JPEG", quality=100) # High quality, large size
    file_obj.seek(0)
    return file_obj

def run():
    print("--- Testing Image Compression ---")
    
    # 1. Create a large dummy image
    print("Generating large image (3000x3000)...")
    img_io = create_large_image()
    original_size = img_io.getbuffer().nbytes
    print(f"Original image size: {original_size / 1024:.2f} KB")
    
    # Setup vehicle
    user, _ = User.objects.get_or_create(username='compression_test_user')
    vt, _ = VehicleType.objects.get_or_create(vehicle_type='Car')
    make, _ = Make.objects.get_or_create(make='TestMake', defaults={})
    make.vehicle_types.add(vt) # Ensure ManyToMany relationship
    model, _ = Model.objects.get_or_create(model='TestModel', make=make, defaults={'vehicle_type': vt})
    seller_type, _ = SellerType.objects.get_or_create(seller_type='Private')

    vehicle, _ = Vehicle.objects.get_or_create(
        owner=user,
        vehicle_type=vt,
        make=make,
        model=model,
        seller_type=seller_type,
        defaults={'price': 1000, 'year': 2020, 'mileage': 10000, 'location': 'Test'}
    )
    
    # 2. Upload image
    print("Uploading image to VehicleImage...")
    uploaded_image = SimpleUploadedFile(name='large_test_image.jpg', content=img_io.read(), content_type='image/jpeg')
    
    v_img = VehicleImage(vehicle=vehicle, image=uploaded_image)
    v_img.save()
    
    # 3. Check saved image
    print(f"Saved image path: {v_img.image.path}")
    saved_size = v_img.image.size
    print(f"Saved image size: {saved_size / 1024:.2f} KB")
    
    # Verify dimensions
    with Image.open(v_img.image.path) as img:
        width, height = img.size
        print(f"Saved image dimensions: {width}x{height}")
        
    if saved_size < original_size:
        print("SUCCESS: Image was compressed.")
    else:
        print("FAILURE: Image size did not decrease.")
        
    if width <= 1920 and height <= 1920:
         print("SUCCESS: Image dimensions are within limits.")
    else:
         print("FAILURE: Image dimensions are too large.")

if __name__ == '__main__':
    run()
