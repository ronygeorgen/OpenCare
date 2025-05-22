from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    email = models.EmailField(unique=True)

    class Meta:
        db_table = 'user'








class VisitedUserData(models.Model):
    email = models.EmailField(unique=True)
    emergency = models.CharField(max_length=100, blank=True)
    factors = models.JSONField(default=list, blank=True)
    lastVisit = models.CharField(max_length=100, blank=True)
    anxiety = models.CharField(max_length=100, blank=True)
    timePreference = models.JSONField(default=list, blank=True)
    hasInsurance = models.CharField(max_length=100, blank=True)
    insuranceProvider = models.CharField(max_length=100, blank=True)
    paymentOption = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.email