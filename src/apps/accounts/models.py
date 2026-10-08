from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

from phonenumber_field.modelfields import PhoneNumberField


# Create your models here.

class UserManager(BaseUserManager):
    # ساخت کاربر از این مسیر، رمز را هش می‌کند و الزام ایمیل و تلفن را بررسی می‌کند.
    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("pleas enter your email")
        if not phone:
            raise ValueError("pleas enter your phone number")
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):
        # حساب مدیریتی به صورت پیش‌فرض فعال است و مجوز ورود به پنل مدیریت دارد.
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone = PhoneNumberField(region="IR", unique=True, null=True, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    acc_created_at = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    # شناسه ورود ایمیل است؛ فرمان createsuperuser شماره تلفن را هم دریافت می‌کند.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone']

    def __str__(self):
        return str(self.email)

    @property
    def full_name(self):
        # اگر هر دو بخش نام موجود نباشد، ایمیل برای نمایش کاربر استفاده می‌شود.
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
