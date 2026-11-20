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

    @classmethod
    def from_db(cls, db, field_names, values):
        instance = super().from_db(db, field_names, values)
        # Remember the status as loaded, so a save can tell whether it changed
        # without another query.
        instance._loaded_status = instance.status if "status" in field_names else None
        return instance

    def __str__(self):
        return self.number
