from django.conf import settings
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        PLACED = "placed", "Placed"
        PAID = "paid", "Paid"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    number = models.CharField(max_length=32, unique=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.PLACED)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.number
