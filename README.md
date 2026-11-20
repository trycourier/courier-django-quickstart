# Order notifications for Django, with Courier

A Django 6 app that emails a customer when their order's status changes, and sends an SMS instead when the email can't go out. A `post_save` signal calls `notify_order_status`, which makes one call to [Courier](https://www.courier.com) through the official Python SDK, [`trycourier`](https://pypi.org/project/trycourier/). Courier picks the channel, delivers, and logs every attempt.

This is the companion project for [Add order notifications by email and SMS to a Django app](https://www.courier.com/docs/guides/add-notifications-to-django) in the Courier docs.

## What it shows

- **The send** in `orders/notifications.py`. It builds the recipient from the Django user, routes email first and SMS second, and sets an idempotency key per order and status.
- **The trigger** in `orders/signals.py`. It sends only when the status actually changed, and only after the transaction commits.
- **A round trip** in `orders/management/commands/send.py`. `python manage.py send` ships one demo order and sends its update to you.

Everything else is a stock Django project: an `Order` model, and a custom user model with a `phone_number` field.

## Run it

You need Python 3.12 or newer and a [Courier account](https://app.courier.com/signup).

```bash
git clone https://github.com/trycourier/courier-django-quickstart.git
cd courier-django-quickstart
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env`:

- `COURIER_API_KEY`: your key from [Platform → API Keys](https://app.courier.com/settings/api-keys). A **Test** key is fine.
- `DEMO_EMAIL`: the address you signed up to Courier with. On a Test key, the built-in test email provider delivers only to members of your workspace.
- `DEMO_PHONE`: optional, in E.164 (`+15551234567`). It's only used if the email can't be sent and you've connected an SMS provider.

Then create the database and send:

```bash
python manage.py migrate
python manage.py send
```

You should see:

```text
Sent shipped update for order ORD-3F9A1C, request id 1-6740a1b2-...
Order ORD-3F9A1C marked shipped. Check you@yourcompany.com, then Courier Logs.
```

The email arrives a few seconds later. Open [Logs](https://app.courier.com/logs) in Courier to see which channel and provider delivered it.

## How the pieces fit

```
order.save()                       Django                              Courier
     |                                |                                    |
     |-- pre_save ------------------->| remember the stored status         |
     |-- post_save ------------------>| status changed?                    |
     |                                |   no  -> nothing                   |
     |                                |   yes -> wait for the commit       |
     |-- COMMIT --------------------->| notify_order_status(order)         |
     |                                |-- POST /send ----------------------->|  route: email, then SMS
     |                                |   Idempotency-Key:                 |
     |                                |   order-ORD-3F9A1C-shipped         |  deliver, log every attempt
     |                                |<-------------- requestId ------------|
```

The idempotency key is the order number plus the status. If the same update is sent twice, by a retry or a race between two saves, Courier returns the first response instead of sending again.

## Adapting it to your app

**Read the phone number from wherever you keep it.** `recipient_for` in `orders/notifications.py` reads `user.email` and `user.phone_number`. If your phone number lives on a profile model, change that one line.

**Keep the `user_id` stable.** The repo maps a Django user to `user_<pk>`. Use the same id everywhere you call Courier, so preferences and logs follow one person.

**Use a template.** The send uses inline `content`, so it runs against a fresh workspace. In production, design the message in Courier, pass `"template": "<your template id>"` instead of `content`, and keep the `data` block as it is.

**Let customers opt out.** This send names no subscription topic, so preferences don't apply to it yet. Map your template to a subscription topic and Courier applies each customer's [preferences](https://www.courier.com/docs/recipients/preferences/overview) to every send.

**Send from a worker.** The send happens after the commit, in the same process. The guide has a short Celery version for sending off the request path.

**Change status with `save()`.** `Order.objects.filter(...).update(status=...)` skips signals, so it sends nothing.

## Commands

| | |
|---|---|
| `python manage.py migrate` | Create the SQLite database |
| `python manage.py send` | Ship one demo order and send its update to `DEMO_EMAIL` |
| `python manage.py check` | Check the project loads |
| `python manage.py runserver` | Run the admin at `localhost:8000/admin` (create a user with `createsuperuser` first). Changing an order's status there sends the update too. |

## Troubleshooting

**`send` printed a request id but no email arrived.** Open the message in [Logs](https://app.courier.com/logs). On a Test key, `DEMO_EMAIL` has to be a member of your Courier workspace. `UNROUTABLE` means no channel could be addressed.

**`AuthenticationError: Error code: 401`.** The key in `.env` is wrong, or it has a stray space. Copy it again.

**Saving an order sends nothing.** That's on purpose when the status didn't change, or when the order was just created. A status that changed back to one already sent within 25 hours is also deduplicated by the idempotency key.

## Further reading

- [Message routing and failover](https://www.courier.com/docs/send/routing)
- [Fall back to another channel when a message isn't delivered](https://www.courier.com/docs/guides/fall-back-when-undelivered), for bounces that arrive after the send
- [Idempotency](https://www.courier.com/docs/reference/api-overview#idempotency)
- [Preferences](https://www.courier.com/docs/recipients/preferences/overview)

## License

MIT
