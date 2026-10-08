from django.shortcuts import render , get_object_or_404
from accounts.models import User
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UpdateProfileSerializer , ChangePasswordSerializer , DeleteAccountSerializer,ProfileSerializer
from accounts.models import User
from .models import Profile
# Create your views here.

def profile_page(request):
    return render(request, 'accounts/profile.html')
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # پروفایل کاربران قدیمی در نخستین درخواست، در صورت نبودن ساخته می‌شود.
        profile, created = Profile.objects.get_or_create(user=request.user)
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)
class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        try:
            profile, created = Profile.objects.get_or_create(user=request.user)
            data = request.data
            print(f"📥 داده: {data}")
            user = request.user
            # این مسیر مستقیماً فیلدهای موجود در درخواست را روی User اعمال می‌کند.
            if 'first_name' in data:
                user.first_name = data['first_name']
            if 'last_name' in data:
                user.last_name = data['last_name']
            if 'phone' in data:
                user.phone = data['phone']
            user.save()
            # نشانی در مدل Profile ذخیره می‌شود و از اطلاعات حساب جداست.
            if 'address' in data:
                profile.address = data['address']
            if 'postal_code' in data:
                profile.postal_code = data['postal_code']
            if 'city' in data:
                profile.city = data['city']
            if 'province' in data:
                profile.province = data['province']
            profile.save()
            return Response({
                'message': 'اطلاعات با موفقیت به‌روزرسانی شد',
                'user': {
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'address': profile.address,
                    'postal_code': profile.postal_code,
                    'city': profile.city,
                    'province': profile.province,
                }
            })     
        except Exception as e:
            print(f"❌ خطا: {str(e)}")
            import traceback
            traceback.print_exc()
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        old_password = serializer.validated_data['old_password']
        new_password = serializer.validated_data['new_password']
        # رمز فعلی با مقدار هش‌شده مقایسه می‌شود؛ رمز تازه نیز با set_password هش می‌شود.
        if not user.check_password(old_password):
            return Response({
                'old_password': 'رمز عبور فعلی اشتباه است'
            }, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(new_password)
        user.save()
        return Response({
            'message': 'رمز عبور با موفقیت تغییر کرد'
        }, status=status.HTTP_200_OK)
class DeleteAccountView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = DeleteAccountSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user
        password = serializer.validated_data['password']
        if not user.check_password(password):
            return Response({
                'password': 'رمز عبور اشتباه است'
            }, status=status.HTTP_400_BAD_REQUEST)
        # حذف کاربر، روابط دارای CASCADE را نیز حذف می‌کند و سپس کوکی‌ها پاک می‌شوند.
        user.delete()
        response = Response({
            'message': 'حساب کاربری با موفقیت حذف شد'
        }, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
class LogoutView(APIView):
    # خروج مرورگر با حذف دو کوکی انجام می‌شود و خود حساب کاربری باقی می‌ماند.
    permission_classes = [IsAuthenticated]
    def post(self, request):
        response = Response({
            'message': 'خروج با موفقیت انجام شد'
        }, status=status.HTTP_200_OK)
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
