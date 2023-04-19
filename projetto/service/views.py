from django.shortcuts import render

from rest_framework import viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated

from residence.models import User
from .serializers import UserSerializer
class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data.get('first_name', ''),
        )
        user.set_password(validated_data['password'])
        user.save()

        return user
