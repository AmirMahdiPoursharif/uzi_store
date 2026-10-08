from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from accounts.models import User
from .models import Profile
import re



class UpdateProfileSerializer(serializers.ModelSerializer):
    # این serializer فیلدهای خود User را پوشش می‌دهد، نه نشانی ذخیره‌شده در Profile.
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name','phone']
    def validate_phone(self, value):
        if value:
            value = re.sub(r'[^0-9]', '', value)
            if value.startswith('0'):
                value = value[1:]
            if value.startswith('98'):
                value = value[2:]
            if len(value) != 10:
                raise serializers.ValidationError("شماره تلفن باید ۱۱ رقم باشد (مثال: 09123456789)")
            value = '0' + value
        return value
    def validate_email(self, value):
        user = self.context['request'].user
        # هنگام بررسی ایمیل تکراری، حساب کاربر جاری از جست‌وجو کنار گذاشته می‌شود.
        if User.objects.filter(email=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("این ایمیل قبلاً توسط کاربر دیگری استفاده شده است")
        return value.lower().strip()
    def validate_first_name(self, value):
        if value and len(value) > 100:
            raise serializers.ValidationError("نام نمی‌تواند بیشتر از 100 کاراکتر باشد")
        return value.strip()
    def validate_last_name(self, value):
        if value and len(value) > 100:
            raise serializers.ValidationError("نام خانوادگی نمی‌تواند بیشتر از 100 کاراکتر باشد")
        return value.strip()
class ChangePasswordSerializer(serializers.Serializer):
    # تطبیق رمز جدید اینجا انجام می‌شود؛ بررسی رمز فعلی بر عهده view است.
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "رمز عبور جدید و تکرار آن مطابقت ندارند"})
        return attrs
class DeleteAccountSerializer(serializers.Serializer):
    # حذف حساب علاوه بر رمز عبور به تأیید صریح کاربر نیاز دارد.
    password = serializers.CharField(required=True, write_only=True)
    confirm = serializers.BooleanField(required=True, write_only=True)
    def validate(self, attrs):
        if not attrs.get('confirm', False):
            raise serializers.ValidationError({"confirm": "برای حذف حساب، باید تایید کنید"})
        return attrs
class ProfileSerializer(serializers.ModelSerializer):
    # sourceهای user.* داده‌های حساب را در کنار فیلدهای نشانی در یک پاسخ نمایش می‌دهند.
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    phone = serializers.CharField(source='user.phone', required=False, allow_blank=True)

    class Meta:
        model = Profile
        fields = [
            'email', 'first_name', 'last_name',
            'address', 'postal_code', 'city', 'province', 'phone',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_phone(self, value):
        if not value:
            return value
        value = re.sub(r'[^0-9]', '', value)
        if value.startswith('0'):
            value = value[1:]
        if value.startswith('98'):
            value = value[2:]
        if len(value) != 10:
            raise serializers.ValidationError("شماره تلفن باید ۱۱ رقم باشد (مثال: 09123456789)")
        value = '0' + value
        user = self.context.get('request').user
        if user and User.objects.filter(phone=value).exclude(id=user.id).exists():
            raise serializers.ValidationError("این شماره تلفن قبلاً ثبت شده است")
        return value

    def validate_postal_code(self, value):
        # کد پستی اختیاری است؛ مقدار غیرخالی بعد از حذف نویسه‌های غیرعددی باید ده رقم باشد.
        if not value:
            return value
        value = re.sub(r'[^0-9]', '', value)
        if len(value) != 10:
            raise serializers.ValidationError("کد پستی باید ۱۰ رقم باشد")
        return value

    def update(self, instance, validated_data):
        user = instance.user

        if 'first_name' in validated_data:
            user.first_name = validated_data.pop('first_name')
        if 'last_name' in validated_data:
            user.last_name = validated_data.pop('last_name')
        if 'phone' in validated_data:
            user.phone = validated_data.pop('phone')
        user.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance
