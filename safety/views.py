from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from .models import SafetyCircle, SafetyCircleMember
from .serializers import SafetyCircleSerializer, SafetyCircleMemberSerializer
from django.shortcuts import get_object_or_404
import random
import string

class SafetyCircleViewSet(viewsets.ModelViewSet):
    serializer_class = SafetyCircleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return circles where the user is a member
        return SafetyCircle.objects.filter(members__user=self.request.user)

    def perform_create(self, serializer):
        # Create the circle and add the owner as an admin member
        circle = serializer.save(owner=self.request.user)
        SafetyCircleMember.objects.create(circle=circle, user=self.request.user, is_admin=True)

    @decorators.action(detail=False, methods=['post'])
    def join(self, request):
        invite_code = request.data.get('invite_code')
        if not invite_code:
            return Response({'error': 'Invite code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            circle = SafetyCircle.objects.get(invite_code=invite_code.upper())
        except SafetyCircle.DoesNotExist:
            return Response({'error': 'Invalid invite code'}, status=status.HTTP_404_NOT_FOUND)
        
        member, created = SafetyCircleMember.objects.get_or_create(circle=circle, user=request.user)
        if not created:
            return Response({'message': 'Already a member of this circle'}, status=status.HTTP_200_OK)
        
        return Response(SafetyCircleSerializer(circle).data, status=status.HTTP_201_CREATED)

    @decorators.action(detail=True, methods=['post'])
    def leave(self, request, pk=None):
        circle = self.get_object()
        try:
            member = SafetyCircleMember.objects.get(circle=circle, user=request.user)
            if member.is_admin and circle.owner == request.user:
                # If owner leaves, maybe transfer ownership or delete circle?
                # For now, just allow leaving if there are other admins or just delete?
                # Life360: owner can't leave without transferring.
                # Simplification: if owner leaves, delete circle if they are the only member.
                if circle.members.count() == 1:
                    circle.delete()
                    return Response({'message': 'Circle deleted as last member left'}, status=status.HTTP_204_NO_CONTENT)
                else:
                    return Response({'error': 'Owner cannot leave circle. Transfer ownership or delete circle.'}, status=status.HTTP_400_BAD_REQUEST)
            
            member.delete()
            return Response({'message': 'Left circle'}, status=status.HTTP_204_NO_CONTENT)
        except SafetyCircleMember.DoesNotExist:
            return Response({'error': 'Not a member of this circle'}, status=status.HTTP_400_BAD_REQUEST)

    @decorators.action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        circle = self.get_object()
        members = circle.members.all()
        serializer = SafetyCircleMemberSerializer(members, many=True)
        return Response(serializer.data)
