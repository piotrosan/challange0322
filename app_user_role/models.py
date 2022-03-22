from django.db import models


class Subscriber(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=150, unique=True)
    gdpr_consent = models.BooleanField(default=True)


class SubscriberSMS(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    phone = models.CharField(max_length=15, unique=True)
    gdpr_consent = models.BooleanField(default=True)


class Client(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=150, unique=True)
    phone = models.CharField(max_length=15)


class User(models.Model):
    create_date = models.DateTimeField(auto_now_add=True)
    email = models.CharField(max_length=150)
    phone = models.CharField(max_length=15, null=True, blank=True)
    gdpr_consent = models.BooleanField(default=True)
