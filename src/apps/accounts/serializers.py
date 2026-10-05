import re

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from rest_framework import serializers

from .models import User


def name_validator(value):
    if value and not re.match(r'^[\u0600-\u06FF\uFB8A\u067E\u0686\u06AF\u200C\u200E\sa-zA-Z]+$', value.strip()):
        raise serializers.ValidationError("نام باید فقط شامل حروف فارسی یا انگلیسی باشد")
    return value.strip()

def validate_phone(self, value):
    value = value.strip()
    value = re.sub(r'[^0-9]', '', value)
    if value.startswith('0'):
        value = value[1:]
    if value.startswith('98'):
        value = value[2:]
    if len(value) != 10:
        raise serializers.ValidationError("شماره تلفن معتبر نیست")
    value = '0' + value
    if User.objects.filter(phone=value).exists():
        raise serializers.ValidationError("این شماره تلفن قبلاً ثبت شده است")
    
    return value
def strong_password_validator(password):
    if not re.search(r'[A-Z]', password):
        raise serializers.ValidationError('رمز عبور باید حداقل یک حرف بزرگ داشته باشد.')
    if not re.search(r'[a-z]', password):
        raise serializers.ValidationError('رمز عبور باید حداقل یک حرف کوچک داشته باشد.')
    if not re.search(r'[0-9]', password):
        raise serializers.ValidationError('رمز باید حداقل شامل یک عدد باشد.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise serializers.ValidationError('رمز باید حداقل شامل یک کاراکتر خاص باشد.')
    return password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True,
                                     validators=[validate_password, strong_password_validator],
                                     style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'password2']

    def validate_email(self, value):
        try:
            EmailValidator()(value)
        except ValidationError:
            raise serializers.ValidationError('فرمت ایمیل وارد شده معبتر نیست.')
        if '..' in value or value.startswith('.') or value.endswith('.'):
            raise serializers.ValidationError('فرمت ایمیل معتبر نیست.')
        banned_emails = ['tempmail.com']
        email = value.split('@')[-1].lower()
        if email in banned_emails:
            raise serializers.ValidationError('ایمیل وارد شده معتبر نمی باشد.')
        value = value.lower().strip()
        if User.objects.filter(email=value, is_active=True).exists():
            raise serializers.ValidationError("این ایمیل قلا استفاده شده است.")
        return value

    def first_name_validate(self, value):
        if value:
            return name_validator(value)
        return ""

    def last_name_validate(self, value):
        if value:
            return name_validator(value)
        return ""
    def validate_phone(self, value):
        """اعتبارسنجی شماره تلفن - فقط عدد، ۱۱ رقم، شروع با 09"""
        value = value.strip()
        value = re.sub(r'[^0-9]', '', value)
        if value.startswith('0'):
            value = value[1:]
        if value.startswith('98'):
            value = value[2:]
        if len(value) != 10:
            raise serializers.ValidationError("شماره تلفن باید ۱۱ رقم باشد (مثال: 09123456789)")
        value = '0' + value
        if User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("این شماره تلفن قبلاً ثبت شده است")
        return value
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError('رمز عبور و تایید با هم مطابقت ندارد.')
        email_check = attrs['email'].split('@')[0].lower()
        password_lower = attrs['password'].lower()
        if email_check in password_lower or password_lower in email_check:
            raise serializers.ValidationError('رمز عبور نباید همانند ایمیل باشد.')
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(
            email=validated_data.get('email'),
            phone=validated_data.get('phone'),  
            password=validated_data.get('password'),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            is_active=False
        )
        return user


class VerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    code = serializers.CharField(max_length=6, min_length=6)
    def validate_phone(self, value):
        value = re.sub(r'[^0-9]', '', value.strip())
        if len(value) != 11 or not value.startswith('09'):
            raise serializers.ValidationError("شماره تلفن معتبر نیست")
        return value
    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError('کد باید عدد باشد.')
        return value

class ResendotpSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15) 
    def validate_phone(self, value):
        value = re.sub(r'[^0-9]', '', value.strip())
        if len(value) != 11 or not value.startswith('09'):
            raise serializers.ValidationError("شماره تلفن معتبر نیست")
        return value
