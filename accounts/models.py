from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # E.164, such as +15551234567. Courier's SMS channel reads it.
    phone_number = models.CharField(max_length=20, blank=True)
