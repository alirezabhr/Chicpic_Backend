from rest_framework.generics import CreateAPIView, GenericAPIView, RetrieveAPIView, UpdateAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.throttling import UserRateThrottle
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

from django.contrib.auth import get_user_model

from .models import UserAdditional
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserReadonlySerializer, \
    OTPRequestSerializer, OTPVerificationSerializer, UserAdditionalSerializer, ResetPasswordSerializer


class OncePerMinuteThrottle(UserRateThrottle):
    rate = '1/minute'


class GoogleAuthentication(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter
    client_class = OAuth2Client


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
    permission_classes = (AllowAny,)
    throttle_classes = (OncePerMinuteThrottle,)

    def post(self, request):
        ser = OTPRequestSerializer(data=request.data)

        if ser.is_valid():
            ser.save()
            return Response(status=status.HTTP_201_CREATED)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        ser = OTPVerificationSerializer(data=request.data)
        if ser.is_valid():
            user = get_user_model().objects.get(email=ser.data.get('email'))
            user.is_verified = True
            user.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


# TODO: Fix security issues. Everyone can change password of any user.
class ResetPasswordView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        ser = ResetPasswordSerializer(data=request.data)
        if ser.is_valid():
            user = get_user_model().objects.get(email=ser.data.get('email'))
            user.set_password(request.data.get('password'))
            user.save()
            return Response(status=status.HTTP_202_ACCEPTED)
        else:
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class UserAdditionalView(CreateAPIView, UpdateAPIView):
    serializer_class = UserAdditionalSerializer
    lookup_field = 'user__id'
    lookup_url_kwarg = 'id'
    queryset = UserAdditional.objects.all()
