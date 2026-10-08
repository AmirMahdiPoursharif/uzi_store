"""
URL configuration for uzistore project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

# هر include پیشوند همان بخش را تعیین می‌کند؛ مسیرهای محصول مستقیماً در ریشه قرار دارند.
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include("product.api.urls")),
    path('order/', include("order.api.user_urls")),
    path('manager/', include("order.api.manager_urls")),
    path('api/auth/', include("accounts.urls")),
    path('cart/', include("cart.api.urls"))
    # مسیر فایل‌های آپلودی به کمک static فقط هنگام فعال بودن DEBUG اضافه می‌شود.
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
