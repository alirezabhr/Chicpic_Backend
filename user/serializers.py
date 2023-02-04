from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from django.contrib.auth import get_user_model
from .models import OTP


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    password2 = serializers.CharField(min_length=8, write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'username', 'is_verified', 'password', 'password2', 'tokens')
        read_only_fields = ('id', 'tokens')

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "Password fields didn't match."})

        return attrs

    def validate_username(self, username):
        if len(username) < 2:
            raise serializers.ValidationError('Username must contain at least 2 characters.')
        if self.Meta.model.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError('User with this username already exists.')

        return username

    def validate_email(self, email):
        if self.Meta.model.objects.filter(email__iexact=self.Meta.model.objects.normalize_email(email)).exists():
            raise serializers.ValidationError('User with this email already exists.')

        return email

    def create(self, validated_data):
        user = self.Meta.model.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password'],
        )
        return user


class UserLoginSerializer(serializers.ModelSerializer):
    username = serializers.CharField(max_length=30)
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = get_user_model()
        fields = ('id', 'email', 'username', 'is_verified', 'password', 'tokens')
        read_only_fields = ('id', 'email', 'tokens')

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            raise AuthenticationFailed('Invalid credentials.')  # It will return 403
        if not user.is_verified:
            raise serializers.ValidationError({'email': 'Your email is not verified.'})

        attrs['id'] = user.id
        attrs['username'] = user.username
        attrs['email'] = user.email
        attrs['is_verified'] = user.is_verified
        attrs['tokens'] = user.tokens()
        return attrs


class OTPRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = '__all__'
        read_only_fields = ('id', 'code', 'created_at', 'expire_at')

    def create(self, validated_data):
        user = validated_data.pop('user')
        otp = OTP.generate_otp(user)
        return otp


class OTPVerifySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    code = serializers.CharField(max_length=10)

    def validate(self, attrs):
        user_id = attrs.get('user_id')
        code = attrs.get('code')

        otp_objects = OTP.objects.filter(user_id=user_id, code=code)

        if not otp_objects.exists():
            raise serializers.ValidationError({'code': 'Code is not valid.'})

        if timezone.now() > otp_objects.first().expire_at:
            raise serializers.ValidationError({'expire_at': 'Code is expired.'})

        return attrs
