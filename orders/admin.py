from django.contrib import admin

from .models import Order

# Change an order's status here and the customer gets the notification.
admin.site.register(Order, list_display=["number", "user", "status", "total"])
