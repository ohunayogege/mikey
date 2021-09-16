from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import AllowAny
# from django.contrib.auth import get_user_model

class CustomUserCreate(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format='json'):
        serializer = CustomUserSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            if user:
                json = serializer.data
                return Response(json, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # def post(self, request, format='None'):
    #     data = self.request.data
        
    #     user_name = data['user_name']
    #     email = data['email']
    #     password = data['password']
    #     password2 = data['password2']

    #     if password == password2:
    #         if User.objects.filter(email=email).exists():
    #             return Response({'error': 'Email already exists'})
    #         else:
    #             if len(password) < 6:
    #                 return Response({'error': 'Password must be at least 6 characters'})
    #             else:
    #                 user = User.objects.create_user(email=email, password=password, user_name=user_name)
    #                 user.save()

    #                 return Response({'success': 'User created successfully'})

    #     else:
    #         return Response({'error': 'Passwords do not match'})

class BlacklistTokenUpdateView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = ()

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)

# class GetUserName(APIView):
#         permission_classes = [AllowAny]

#         def get(self, request, format=None):
#             user = NewUser.objects.all()
#             serializer = CustomUserSerializer(user, many=True)
#             return Response(serializer.data)

#             # if serializer.is_valid():
#             #     json = serializer.data.user_name
#             #     return Response(json, status=status.HTTP_201_CREATED)



