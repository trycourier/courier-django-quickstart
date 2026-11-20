# Courier Django quickstart

A Django 6 app that sends an order status notification (email first, SMS if the email can't be sent) through Courier when `Order.status` changes. Guide: https://www.courier.com/docs/guides/add-notifications-to-django

## Commands

- Install: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Set up: `cp .env.example .env`, then `python manage.py migrate`
- Send one demo update: `python manage.py send` (prints a request id)
- Check: `python manage.py check`
- Admin: `python manage.py runserver`, then `/admin/orders/order/`

## Environment

Read from `.env` by `shop/settings.py` (python-dotenv). Never commit `.env`.

- `COURIER_API_KEY`: read in `orders/notifications.py`. Server-side only.
- `DEMO_EMAIL`, `DEMO_PHONE`: read only by the `send` command.

## Files that matter

- `orders/notifications.py`: `notify_order_status(order, idempotency_key)`, the one `client.send.message` call. `recipient_for` maps a Django user to a Courier recipient.
- `orders/signals.py`: sends on a real status change, after commit, with one key per change.
- `orders/models.py`: `Order`. `from_db` and `refresh_from_db` remember the loaded status.
- `orders/management/commands/send.py`: ships one demo order through the signal.
- `accounts/models.py`: custom user with `phone_number` (E.164).

## Rules

- Use the `trycourier` package (`from courier import Courier`). Read the key from `COURIER_API_KEY`, never hard-code it.
- Pass an idempotency key on every send. Build it once per status change and reuse it on retries.
- Keep the status-change guard and `transaction.on_commit`. Removing either sends duplicates or notifies on rolled-back saves.
- Change status with `save()`. `QuerySet.update()` skips signals.
- Don't call a provider SDK (Twilio, SendGrid) directly. Courier routes to the providers connected in the workspace.
