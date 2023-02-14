from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from django.utils import timezone

from django.contrib.auth import get_user_model
from .models import OTP


User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(min_length=8, write_only=True, required=True)
    password2 = serializers.CharField(min_length=8, write_only=True, required=True)

    class Meta:
        model = User
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
        model = User
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


class UserReadonlySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'username', 'is_verified', 'tokens')
        read_only_fields = ('id', 'email', 'username', 'is_verified', 'tokens')


class OTPRequestSerializer(serializers.Serializer):
    user = None
    email = serializers.EmailField()

    def validate_email(self, email):
        try:
            self.user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return email

    def create(self, validated_data):
        return OTP.generate_otp(self.user)


class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        otp = OTP.objects.filter(user=user, code=attrs['code']).order_by('-created_at').first()
        if not otp:
            raise serializers.ValidationError({"code": "Code is not valid."})
        if otp.expire_at < timezone.now():
            raise serializers.ValidationError({"code": "OTP code has expired."})
        return attrs
