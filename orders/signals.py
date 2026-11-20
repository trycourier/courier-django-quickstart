from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Order
from .notifications import notify_order_status


@receiver(pre_save, sender=Order)
def remember_previous_status(sender, instance, **kwargs):
    # Read the stored status before this save overwrites it.
    instance._previous_status = (
        Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        if instance.pk
        else None
    )


@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, raw, **kwargs):
    # New orders and fixture loads aren't status changes.
    if created or raw or instance.status == instance._previous_status:
        return

    # Send once the transaction commits, so a rolled-back save notifies nobody.
    # robust=True logs a failed send instead of raising it into your view.
    transaction.on_commit(lambda: notify_order_status(instance), robust=True)
