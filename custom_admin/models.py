from django.db import models

# Create your models here.

class Users(models.Model):
    name = models.CharField(max_length=35)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)

class Contactus(models.Model):
    firstname = models.CharField(max_length=35)
    email = models.EmailField(unique=False)
    message = models.TextField(blank=False)
    userid = models.IntegerField()