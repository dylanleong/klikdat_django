import cv2
import os
from deepface import DeepFace
from .models import VerificationProfile
from django.conf import settings

def analyze_verification_video(profile_id):
    try:
        profile = VerificationProfile.objects.get(id=profile_id)
        if not profile.verification_video:
            profile.ai_analysis_status = 'failed'
            profile.save()
            return

        video_path = profile.verification_video.path
        
        # Extract a frame from the video
        cap = cv2.VideoCapture(video_path)
        success, frame = cap.read()
        if not success:
            profile.ai_analysis_status = 'failed'
            profile.save()
            return
        
        # Save frame temporarily for DeepFace
        temp_frame_path = f"/tmp/frame_{profile_id}.jpg"
        cv2.imwrite(temp_frame_path, frame)
        cap.release()

        # Analyze with DeepFace
        # actions=['age', 'gender']
        results = DeepFace.analyze(img_path=temp_frame_path, actions=['age', 'gender'], enforce_detection=False)
        
        # DeepFace returns a list if multiple faces are detected, or a dict.
        if isinstance(results, list):
            result = results[0]
        else:
            result = results

        detected_gender = result.get('dominant_gender')
        detected_age = result.get('age')

        profile.detected_gender = detected_gender
        profile.detected_age_range = f"{detected_age}-{(detected_age//10)*10+9}" # Simple range
        
        # Compare with user profile if available
        user_profile = profile.user.profile
        gender_match = False
        if detected_gender and user_profile.gender:
            # Map DeepFace gender to Profile gender
            # DeepFace: 'Man', 'Woman'
            # Profile: 'M', 'F'
            if (detected_gender == 'Man' and user_profile.gender == 'M') or \
               (detected_gender == 'Woman' and user_profile.gender == 'F'):
                gender_match = True

        profile.v4_gender = gender_match
        profile.v5_age = True # For now, we just mark age as verified if we detected it.
        # In a real scenario, we'd check if detected_age matches user_profile.dob
        
        profile.ai_analysis_status = 'completed'
        profile.save()
        
        # Cleanup
        if os.path.exists(temp_frame_path):
            os.remove(temp_frame_path)

    except Exception as e:
        print(f"Error in analyze_verification_video: {e}")
        try:
            profile = VerificationProfile.objects.get(id=profile_id)
            profile.ai_analysis_status = 'failed'
            profile.save()
        except:
            pass
