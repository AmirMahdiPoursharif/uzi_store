# accounts_app/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # در صورت وجود هدر احراز هویت، بررسی آن بر کوکی اولویت دارد.
        header = self.get_header(request)
        if header is not None:
            return super().authenticate(request)
        # مرورگر توکن را همراه کوکی می‌فرستد؛ نبود آن یعنی این روش کاربری تشخیص نداده است.
        access_token = request.COOKIES.get('access_token')
        if not access_token:
            return None
        try:
            # اعتبار توکن و کاربر وابسته به آن با قواعد خود SimpleJWT بررسی می‌شود.
            validated_token = self.get_validated_token(access_token)
            user = self.get_user(validated_token)
            return (user, validated_token)
        except InvalidToken:
            raise AuthenticationFailed('توکن نامعتبر است')
