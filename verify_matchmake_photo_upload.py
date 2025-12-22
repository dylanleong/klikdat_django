import os
import django
import sys
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

# Setup Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'klikdat_django.settings')
django.setup()

from django.contrib.auth.models import User
from matchmake.models import MatchmakeProfile, MatchmakePhoto
from matchmake.serializers import MatchmakePhotoSerializer
from rest_framework.test import APIRequestFactory, force_authenticate
from matchmake.views import MatchmakePhotoViewSet

def create_image(width=100, height=100, color='red'):
    file_obj = BytesIO()
    image = Image.new("RGB", (width, height), color)
    image.save(file_obj, format="JPEG")
    file_obj.seek(0)
    return file_obj

def run():
    print("--- Testing Matchmake Photo Upload ---")
    
    # 1. Create a user and profile
    username = 'photo_test_user'
    email = 'photo@test.com'
    
    # Cleanup
    try:
        u = User.objects.get(username=username)
        u.delete()
    except User.DoesNotExist:
        pass
        
    user = User.objects.create_user(username=username, email=email, password='password')
    profile, _ = MatchmakeProfile.objects.get_or_create(user=user)
    print(f"Created user and profile for: {username}")
    
    factory = APIRequestFactory()
    view = MatchmakePhotoViewSet.as_view({'post': 'create', 'get': 'list', 'delete': 'destroy'})

    # 2. Test Upload
    print("Uploading photo...")
    img_io = create_image()
    photo_file = SimpleUploadedFile(name='test_match.jpg', content=img_io.read(), content_type='image/jpeg')
    
    request = factory.post('/api/matchmake/photos/', {'image': photo_file}, format='multipart')
    force_authenticate(request, user=user)
    
    response = view(request)
    
    if response.status_code == 201:
        print(f"SUCCESS: Photo uploaded. ID: {response.data['id']}")
        photo_id = response.data['id']
    else:
        print(f"FAILURE: Upload failed. Status: {response.status_code}, Data: {response.data}")
        return

    # 3. Test List
    print("Listing photos...")
    request = factory.get('/api/matchmake/photos/')
    force_authenticate(request, user=user)
    response = view(request)
    
    if response.status_code == 200 and len(response.data) > 0:
         print(f"SUCCESS: Photo found in list. Count: {len(response.data)}")
    else:
         print(f"FAILURE: Photo not in list or list failed. Status: {response.status_code}, Data: {response.data}")

    # 4. Test Delete
    print(f"Deleting photo {photo_id}...")
    request = factory.delete(f'/api/matchmake/photos/{photo_id}/')
    force_authenticate(request, user=user)
    response = view(request, pk=photo_id)
    
    if response.status_code == 204:
        print("SUCCESS: Photo deleted.")
        if not MatchmakePhoto.objects.filter(id=photo_id).exists():
            print("Verified: Photo record removed from DB.")
        else:
            print("FAILURE: Photo record still exists in DB!")
    else:
        print(f"FAILURE: Delete failed. Status: {response.status_code}")

if __name__ == '__main__':
    run()
