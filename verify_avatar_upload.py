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
from users.models import Profile

def create_image(width=100, height=100, color='blue'):
    file_obj = BytesIO()
    image = Image.new("RGB", (width, height), color)
    image.save(file_obj, format="JPEG")
    file_obj.seek(0)
    return file_obj

def run():
    print("--- Testing Avatar Upload ---")
    
    # 1. Create a user
    username = 'avatar_test_user'
    email = 'avatar@test.com'
    
    # Cleanup
    try:
        u = User.objects.get(username=username)
        u.profile.delete()
        u.delete()
    except User.DoesNotExist:
        pass
    except Exception:
        pass # Profile might not exist if signal failed or something
        
    user = User.objects.create_user(username=username, email=email, password='password')
    print(f"Created user: {username}")
    
    # Check if profile was created by signal
    try:
        profile = user.profile
        print("SUCCESS: Profile created automatically by signal.")
    except Exception as e:
        print(f"FAILURE: Profile NOT created. Error: {e}")
        return

    # 2. Upload avatar via Serializer (simulating API)
    # Actually, let's verify if we can assign avatar to profile directly first, 
    # then check if we can reach it via user.profile.avatar
    
    print("Uploading avatar...")
    img_io = create_image()
    avatar_file = SimpleUploadedFile(name='avatar.jpg', content=img_io.read(), content_type='image/jpeg')
    
    profile.avatar = avatar_file
    profile.save()
    
    print(f"Saved avatar path: {profile.avatar.path}")
    
    if profile.avatar:
         print("SUCCESS: Avatar saved to profile.")
    else:
         print("FAILURE: Avatar not saved.")

    # 3. Simulate UserSerializer update (nested)
    # We need to import serializer
    from users.serializers import UserSerializer
    
    print("\nTesting UserSerializer update with avatar...")
    img_io2 = create_image(color='green')
    avatar_file2 = SimpleUploadedFile(name='avatar2.jpg', content=img_io2.read(), content_type='image/jpeg')
    
    # Serializer expects 'profile' dict with 'avatar' inside? 
    # Wait, my serializer implementation:
    # avatar = serializers.ImageField(source='profile.avatar', ...)
    # This means it expects 'avatar' at top level of data, and writes to profile.avatar.
    # Ah, I need to check my serializer implementation in `users/serializers.py`!
    
    data = {'avatar': avatar_file2}
    serializer = UserSerializer(instance=user, data=data, partial=True)
    
    if serializer.is_valid():
        user = serializer.save()
        print(f"Serializer updated avatar to: {user.profile.avatar.name}")
        if 'avatar2' in user.profile.avatar.name:
            print("SUCCESS: UserSerializer updated avatar correctly.")
        else:
             print("FAILURE: UserSerializer did not update avatar properly.")
    else:
        print(f"FAILURE: Serializer invalid. Errors: {serializer.errors}")

if __name__ == '__main__':
    run()
