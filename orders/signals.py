from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order
from .notifications import notify_order_status


@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, raw, **kwargs):
    previous = getattr(instance, "_loaded_status", None)
    instance._loaded_status = instance.status

    # New orders and fixture loads aren't status changes.
    if created or raw or instance.status == previous:
        return

    # One key per status change. Retries of this send reuse it, and a later
    # change back to the same status gets a new one.
    key = f"order-{instance.number}-{instance.status}-{timezone.now():%Y%m%d%H%M%S}"

    # Send once the transaction commits, so a rolled-back save notifies nobody.
    # robust=True logs a failed send instead of raising it into your view.
    transaction.on_commit(lambda: notify_order_status(instance, key), robust=True)
