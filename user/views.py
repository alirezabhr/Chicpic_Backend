from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle

from django.contrib.auth import get_user_model

from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserReadonlySerializer,\
    OTPRequestSerializer, OTPVerifySerializer


class OncePerMinuteThrottle(UserRateThrottle):
    rate = '1/minute'


class SignupView(CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = (AllowAny,)


class LoginView(GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        ser = self.serializer_class(data=request.data)
        if ser.is_valid():
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(RetrieveAPIView):
    serializer_class = UserReadonlySerializer
    queryset = get_user_model().objects.all()

    def get_object(self):
        return self.request.user


class RequestOTPView(APIView):
    throttle_classes = (OncePerMinuteThrottle,)

    def post(self, request):
        ser = OTPRequestSerializer(data=request.data)

        if ser.is_valid():
            ser.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    def post(self, request):
        ser = OTPVerifySerializer(data=request.data)
        if ser.is_valid():
            user = get_user_model().objects.get(id=ser.data.get('user_id'))
            user.is_verified = True
            user.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
