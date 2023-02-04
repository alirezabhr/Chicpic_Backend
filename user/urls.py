from django.urls import path

from . import views


urlpatterns = [
    path('signup/', views.SignupView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('otp/request/', views.RequestOTPView.as_view(), name='request_otp'),
    path('otp/verify/', views.VerifyOTPView.as_view(), name='verify_otp'),
]
