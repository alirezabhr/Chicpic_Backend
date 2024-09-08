from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


urlpatterns = [
    path('social-auth/google/', views.GoogleAuthentication.as_view(), name='google_auth'),
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('check-auth/', views.UserCheckAuthView.as_view(), name='user_check_authentication'),
    path('otp/request/', views.RequestOTPView.as_view(), name='request_otp'),
    path('otp/verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('reset-password/', views.ResetPasswordView.as_view(), name='reset_password'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('<int:id>/', views.UserView.as_view(), name='user_details'),
    path('<int:id>/additional/', views.UserAdditionalView.as_view(), name='user_additional'),
]
