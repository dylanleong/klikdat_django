from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Interest(models.Model):
    name = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return self.name

class MatchmakeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='matchmake_profile')
    bio = models.TextField(blank=True, null=True)
    intro_video = models.FileField(upload_to='matchmake_intros/', null=True, blank=True)
    
    # Lifestyle
    SMOKING_CHOICES = [('Never', 'Never'), ('Socially', 'Socially'), ('Regularly', 'Regularly')]
    DRINKING_CHOICES = [('Never', 'Never'), ('Socially', 'Socially'), ('Regularly', 'Regularly')]
    EXERCISE_CHOICES = [('Never', 'Never'), ('Sometimes', 'Sometimes'), ('Active', 'Active'), ('Athletic', 'Athletic')]
    
    smoking = models.CharField(max_length=20, choices=SMOKING_CHOICES, blank=True, null=True)
    drinking = models.CharField(max_length=20, choices=DRINKING_CHOICES, blank=True, null=True)
    exercise = models.CharField(max_length=20, choices=EXERCISE_CHOICES, blank=True, null=True)
    dietary_preferences = models.CharField(max_length=100, blank=True, null=True)
    education = models.CharField(max_length=100, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True, null=True)
    
    RELATIONSHIP_GOAL_CHOICES = [
        ('Long-term', 'Long-term relationship'),
        ('Short-term', 'Short-term relationship'),
        ('Casual', 'Casual dating'),
        ('Friendship', 'Friendship'),
        ('Not Sure', 'Not sure yet'),
    ]
    relationship_goal = models.CharField(max_length=50, choices=RELATIONSHIP_GOAL_CHOICES, blank=True, null=True)
    
    # New detailed fields
    height = models.IntegerField(null=True, blank=True, help_text='In centimeters')
    ethnicity = models.CharField(max_length=100, blank=True, null=True)
    languages_spoken = models.CharField(max_length=255, blank=True, null=True)
    
    # Long-term relationship advising info
    pets = models.CharField(max_length=100, blank=True, null=True)
    religion = models.CharField(max_length=100, blank=True, null=True)
    politics = models.CharField(max_length=100, blank=True, null=True)
    future_family_plans = models.CharField(max_length=255, blank=True, null=True)
    zodiac = models.CharField(max_length=50, blank=True, null=True)

    interests = models.ManyToManyField(Interest, blank=True)
    
    # Preferences for Discovery
    pref_min_age = models.IntegerField(default=18, validators=[MinValueValidator(18)])
    pref_max_age = models.IntegerField(default=99)
    pref_max_distance = models.IntegerField(default=50, help_text='In kilometers')
    pref_looking_for = models.CharField(max_length=20, default='Everyone') # 'M', 'F', 'O', 'Everyone'
    
    @property
    def profile_completeness(self):
        # Basic fields that should be filled
        fields = [
            self.bio, self.smoking, self.drinking, self.exercise, 
            self.dietary_preferences, self.education, self.profession,
            self.relationship_goal, self.height, self.ethnicity, 
            self.languages_spoken, self.pets, self.religion, 
            self.politics, self.future_family_plans, self.zodiac
        ]
        filled = sum(1 for f in fields if f)
        return int((filled / len(fields)) * 100)
    
    def __str__(self):
        return f"{self.user.username}'s Matchmake Profile"

class MatchmakePhoto(models.Model):
    profile = models.ForeignKey(MatchmakeProfile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='matchmake_photos/')
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Swipe(models.Model):
    swiper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_made')
    swiped = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes_received')
    is_like = models.BooleanField() # True for swipe right, False for swipe left
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('swiper', 'swiped')

class Match(models.Model):
    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches2')
    chat_room = models.OneToOneField('chat.ChatRoom', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user1', 'user2')
