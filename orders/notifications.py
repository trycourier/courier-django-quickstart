import functools
import logging
import os

from courier import Courier

logger = logging.getLogger(__name__)


@functools.cache
def courier() -> Courier:
    # Created on the first send, so migrations and `manage.py check` run without a key.
    return Courier(api_key=os.environ["COURIER_API_KEY"])


def recipient_for(user) -> dict:
    """Map a Django user to a Courier recipient."""
    # Use the same user_id everywhere you call Courier, so preferences follow the person.
    to = {"user_id": f"user_{user.pk}"}
    if user.email:
        to["email"] = user.email
    if user.phone_number:
        to["phone_number"] = user.phone_number
    return to


def notify_order_status(order, idempotency_key: str) -> str:
    """Tell the customer their order's status changed. Returns Courier's request id."""
    status = order.get_status_display()
    response = courier().send.message(
        message={
            "to": recipient_for(order.user),
            # Email first. Courier moves to SMS if the email can't be sent.
            "routing": {"method": "single", "channels": ["email", "sms"]},
            "content": {
                "title": f"Order {order.number}: {status}",
                "body": f"Hi {order.user.first_name or 'there'}, order {order.number} is now {status.lower()}.",
            },
            "data": {
                "order_number": order.number,
                "status": order.status,
                "total": float(order.total),
            },
        },
        # One key per status change. A repeat with this key returns the first
        # response instead of sending again.
        idempotency_key=idempotency_key,
    )
    logger.info("Sent %s update for order %s, request id %s", order.status, order.number, response.request_id)
    return response.request_id
