import logging

from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny , IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, VerifySerializer, ResendotpSerializer
from .utils import otp_generate, otp_verify
from django.shortcuts import render
from .models import User

# Create your views here.
User = get_user_model()
loger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class RegisterThrottle(AnonRateThrottle):
    rate = '3/hour'


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]
    authentication_classes = []
    def create(self, request, *args, **kwargs):
        phone = request.data.get('phone', '').strip()
        email = request.data.get('email', '').lower().strip()
        client_ip = get_client_ip(request)
        loger.info(f'Registration attempt for phone: {phone[:3]}*** from ip: {client_ip}')
        if not email or '@' not in email:
            return Response({'message': 'لطفا ایمیل معتبر وارد کنید.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not phone:
            return Response({'message': 'لطفا شماره تلفن را وارد کنید.'}, status=status.HTTP_400_BAD_REQUEST)

        ip_key = f'register_ip_{client_ip}'
        ip_attempts = cache.get(ip_key, 0)
        if ip_attempts >= 5:
            return Response({'message': 'درخواست بیش از حد است لطفا بعدا تلاش کنید.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        user_exists = User.objects.filter(email=email).exists() or User.objects.filter(phone=phone).exists()
        
        if user_exists:
            user = User.objects.filter(email=email).first() or User.objects.filter(phone=phone).first()
            if user.is_active:
                return Response({'message': 'این حساب قبلا تایید شده است.'}, status=status.HTTP_200_OK)
            otp = otp_generate(phone)
            cache.set(ip_key, ip_attempts + 1, timeout=3600)
            return Response({'message': 'کد جدید به شماره تلفن شما ارسال شد.'}, status=status.HTTP_200_OK)
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if 'password' in str(serializer.errors):
                return Response({'message': 'رمز باید حداقل شامل ۸ کاراکتر و حرف بزرگ و حرف کوچک و عدد باشد.'},
                                status=status.HTTP_400_BAD_REQUEST)
            return Response({'message': str(serializer.errors)}, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        otp = otp_generate(phone)
        cache.set(ip_key, ip_attempts + 1, timeout=3600)
        return Response({'message': 'کد تایید به شماره تلفن شما ارسال شد.'}, status=status.HTTP_201_CREATED)


class VerifyThrottle(AnonRateThrottle):
    rate = '10/hour'


class VerifyView(views.APIView):
    permission_classes = [AllowAny]
    throttle_classes = [VerifyThrottle]

    def post(self, request):
        serializer = VerifySerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'message': 'اطلاعات وارد شده معتبر نیست.'}, status=status.HTTP_400_BAD_REQUEST)
        
        phone = serializer.validated_data['phone'] 
        code = serializer.validated_data['code']
        client_ip = get_client_ip(request)
        
        email_attempt_key = f'verify_block_{phone}'
        attempts = cache.get(email_attempt_key, 0)
        if attempts >= 5:
            cache.set(f'verify_block_{phone}', True, timeout=900)
            return Response({'message': 'تعداد تلاش‌های شما بیش از حد مجاز است لطفا ۱۵ دقیقه بعد تلاش کنید.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            user = User.objects.get(phone=phone) 
        except User.DoesNotExist:
            loger.warning(f'Verify attempt for non-existent phone: {phone[:3]}***')
            return Response({'message': 'کاربری با این شماره تلفن یافت نشد.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if user.is_active:
            return Response({'message': 'این حساب قبلا تایید شده است.'}, status=status.HTTP_200_OK)
        
        if otp_verify(phone, code):
            user.is_active = True
            user.save()
            cache.delete(email_attempt_key)
            cache.delete(f'verify_block_{phone}')
            loger.info(f"User verified successfully: {phone[:3]}***")
            return Response({'message': 'شماره تلفن با موفقیت تأیید شد. حالا می‌توانید وارد شوید.'},
                            status=status.HTTP_200_OK)

        new_attempts = attempts + 1
        cache.set(email_attempt_key, new_attempts, timeout=3600)
        loger.warning(f"Invalid OTP for {phone[:3]}*** from IP: {client_ip}")
        cached_code = cache.get(f'otp_{phone}')
        remaining_attempts = 5 - new_attempts
        if cached_code and str(cached_code) != str(code):
            if remaining_attempts > 0:
                return Response({
                    'message': f'کد وارد شده اشتباه است. {remaining_attempts} تلاش دیگر دارید.',
                    'remaining_attempts': remaining_attempts
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'message': 'کد وارد شده اشتباه است. تعداد تلاش‌های شما به پایان رسیده است.'},
                                status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'message': 'کد تأیید منقضی شده است. لطفاً درخواست کد جدید دهید.'},
                            status=status.HTTP_400_BAD_REQUEST)

class ResendotpView(views.APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendotpSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'message': 'ایمیل معتبر وارد کنید'}, status=status.HTTP_400_BAD_REQUEST)
        email = serializer.validated_data['email'].lower().strip()
        client_ip = get_client_ip(request)
        last_sent = cache.get(f'resend_otp_{email}')
        if last_sent:
            return Response({'message': 'لطفاً ۲ دقیقه صبر کنید تا دوباره تلاش کنید'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        ip_resend_key = f'resend_ip_{client_ip}'
        ip_resend_attempts = cache.get(ip_resend_key, 0)
        if ip_resend_attempts >= 10:
            return Response({'message': 'درخواست بیش از حد از این IP. لطفاً بعداً تلاش کنید.'},
                            status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({'message': 'این حساب قبلاً تأیید شده است. لطفاً وارد شوید.'},
                                status=status.HTTP_400_BAD_REQUEST)
            otp = otp_generate(email)
            send_otp_email(email, otp)
            cache.set(f'resend_otp_{email}', True, timeout=120)
            cache.set(ip_resend_key, ip_resend_attempts + 1, timeout=3600)
            return Response({'message': 'کد تأیید جدید به ایمیل شما ارسال شد'}, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            loger.info(f"Resend OTP for non-existent email: {email[:3]}***")
            return Response({'message': 'اگر این ایمیل ثبت شده باشد، کد تأیید ارسال خواهد شد'},
                            status=status.HTTP_200_OK)


class LoginThrottle(AnonRateThrottle):
    rate = '5/minute'

class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email', '').lower().strip()
        client_ip = get_client_ip(request)
        loger.info(f"Login attempt for email: {email[:3]}*** from IP: {client_ip}")
        ip_fail_key = f'login_fail_ip_{client_ip}'
        ip_fails = cache.get(ip_fail_key, 0)
        if ip_fails >= 10:
            return Response({'message': 'از این IP درخواست بیش از حد مجاز است. ۱۵ دقیقه دیگر تلاش کنید.'},
                 status=status.HTTP_429_TOO_MANY_REQUESTS)
        user_fail_key = f'login_fail_user_{email}'
        user_fails = cache.get(user_fail_key, 0)
        if user_fails >= 5:
            return Response({'message': 'حساب کاربری شما موقتاً قفل شده است. لطفاً ۱۵ دقیقه دیگر تلاش کنید.'},
              status=status.HTTP_423_LOCKED)
        if email:
            try:
                user = User.objects.get(email=email)
                if not user.is_active:
                    return Response({'message': 'لطفاً ابتدا ایمیل خود را تأیید کنید.'},
                      status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                pass
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            user = User.objects.get(email=email)
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            cache.delete(user_fail_key)
            cache.delete(ip_fail_key)
            loger.info(f"successful login for email: {email[:3]}***")
            response = Response({
                'message': 'ورود با موفقیت انجام شد',
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                }},
              status=status.HTTP_200_OK)
            response.set_cookie(
                key='access_token',
                value=access_token,
                httponly=True,     
                secure=False,       
                samesite='Lax',     
                max_age=60 * 15,    
                path='/',
            )
            response.set_cookie(
                key='refresh_token',
                value=refresh_token,
                httponly=True,
                secure=False,
                samesite='Lax',
                max_age=60 * 60 * 24,  
                path='/',
            )
            return response
        except AuthenticationFailed:
            cache.set(user_fail_key, user_fails + 1, timeout=900)
            cache.set(ip_fail_key, ip_fails + 1, timeout=900)
            loger.warning(f"Failed login for {email[:3]}*** from IP: {client_ip}")
            return Response({'message': 'ایمیل یا رمز عبور اشتباه است'},
              status=status.HTTP_401_UNAUTHORIZED)

class LogoutView(views.APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        response = Response({'message': 'خروج با موفقیت انجام شد'})
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

def register_page(request):
    return render(request, 'accounts/register.html')

def verify_page(request):
    return render(request, 'accounts/verify.html')

def login_page(request):
    return render(request, 'accounts/login.html')

#TODO
# send email in terminal
# set register rate limit to success register 5/day
# add "verified" field in models and dont create user modelo without verify email
# postman / pycharm
# banned email change to accepted email
# login with cookie \ check tokens to not visible
# **in panel admin the user password must be read only
# **Automate the refreshing and updating tokens