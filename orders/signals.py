from django.db import transaction
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Order
from .notifications import notify_order_status


@receiver(pre_save, sender=Order)
def load_stored_status(sender, instance, raw, **kwargs):
    # Orders loaded with their status skip this. One loaded without it, such as
    # Order.objects.only("total"), reads the stored status once.
    if instance.pk and not raw and not hasattr(instance, "_loaded_status"):
        instance._loaded_status = Order.objects.filter(pk=instance.pk).values_list("status", flat=True).first()


@receiver(post_save, sender=Order)
def notify_on_status_change(sender, instance, created, raw, **kwargs):
    status = instance.status

    def remember():
        instance._loaded_status = status

    # New orders and fixture loads aren't status changes.
    if created or raw:
        transaction.on_commit(remember)
        return
    if status == instance._loaded_status:
        return

    # One key per status change. Retries of this send reuse it, and a later
    # change back to the same status gets a new one.
    key = f"order-{instance.number}-{status}-{timezone.now():%Y%m%d%H%M%S%f}"

    def send():
        remember()
        notify_order_status(instance, key)

    # Send once the transaction commits, so a rolled-back save notifies nobody
    # and a retried save still does. robust=True logs a failed send instead of
    # raising it into your view.
    transaction.on_commit(send, robust=True)
