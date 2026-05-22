import uuid
import random
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.
class OrderStatus(models.IntegerChoices):
    payment = 1, _('payment')
    preparing = 2, _('preparing')
    sent = 3, _('sent')
    delivered = 4, _('delivered')
    canceled = 5, _('canceled')


class Order(models.Model):
    order_id = models.IntegerField(unique=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=OrderStatus.choices,)
    total_price = models.PositiveIntegerField(default=0)

    def order_id_generator(self):
        return self.order_id == random.randint(1, 100000)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # product = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()