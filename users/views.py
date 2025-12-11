from django.contrib.auth.models import User
from rest_framework import viewsets, permissions
from .serializers import UserSerializer

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Optionally restrict so users can only see themselves unless admin
        # For now, following plan to list all, but let's implement basic filtering if needed.
        return super().get_queryset()
