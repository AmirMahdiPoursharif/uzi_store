from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from dashboard.views import ProfileView, UpdateProfileView, ChangePasswordView, DeleteAccountView, LogoutView, \
    profile_page
from .views import RegisterView, VerifyView, ResendotpView, CustomTokenObtainPairView, verify_page, register_page, \
    login_page

# این مسیرها زیر پیشوند api/auth/ نصب می‌شوند و API پروفایل را هم در بر می‌گیرند.
urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify/", VerifyView.as_view(), name="verify"),
    path("api/auth/resend-otp/", ResendotpView.as_view(), name="resend-otp"),
    path("login/", CustomTokenObtainPairView.as_view(), name="login"),
    # view استاندارد refresh، توکن تازه‌سازی را از بدنه درخواست می‌خواند.
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path('api/auth/logout/', LogoutView.as_view(), name='logout'),
    path('verify-page/', verify_page, name='verify-page'),
    path('register-page/', register_page, name='register-page'),
    path('login-page/', login_page, name='login-page'),
    path('profile-page/', profile_page, name='profile-page'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('update-profile/', UpdateProfileView.as_view(), name='update-profile'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('delete-account/', DeleteAccountView.as_view(), name='delete-account'),
    path('resend-otp/', ResendotpView.as_view(), name='resend-otp'),
]
