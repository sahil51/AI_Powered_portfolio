from django.shortcuts import render
from rest_framework import generics
from .models import User
from .serializers import RegisterSerializers
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializers import UserProfileSerializer

class RegisterView(
    generics.CreateAPIView
):
    queryset = User.objects.all()
    serializer_class = (
        RegisterSerializers
    )
class ProfileView(APIView):
    permission_classes=[IsAuthenticated]
    
    def get(self,request):
        serializer =(UserProfileSerializer(request.user))
        return Response(serializer.data)