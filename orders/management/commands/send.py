import os
import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from orders.models import Order


class Command(BaseCommand):
    help = "Ship one demo order, which sends its status update to DEMO_EMAIL."

    def handle(self, *args, **options):
        if not os.environ.get("COURIER_API_KEY"):
            raise CommandError("COURIER_API_KEY is not set. Copy .env.example to .env and add your key.")
        email = os.environ.get("DEMO_EMAIL")
        if not email or email == "YOUR_EMAIL":
            raise CommandError("DEMO_EMAIL is not set. Put your own email address in .env.")

        # pk 123 becomes Courier user_id "user_123". Your app already has its users.
        user, _ = get_user_model().objects.update_or_create(
            pk=123,
            defaults={
                "username": "sarah",
                "first_name": "Sarah",
                "email": email,
                "phone_number": os.environ.get("DEMO_PHONE", ""),
            },
        )

        # Creating an order sends nothing. Changing its status sends one notification.
        order = Order.objects.create(user=user, number=f"ORD-{secrets.token_hex(3).upper()}", total=Decimal("79.99"))
        order.status = Order.Status.SHIPPED
        order.save()

        self.stdout.write(f"Order {order.number} marked shipped. Check {email}, then Courier Logs.")
