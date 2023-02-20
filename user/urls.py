from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('details/', views.UserDetailView.as_view(), name='user_detail'),
    path('otp/request/', views.RequestOTPView.as_view(), name='request_otp'),
    path('otp/verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
    path('token/refresh/', TokenRefreshView.as_view(), name='refresh_token'),
    path('additional/', views.UserAdditionalView.as_view(), name='user_additional'),
]
