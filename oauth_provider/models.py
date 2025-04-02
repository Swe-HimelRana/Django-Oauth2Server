from django.db import models, transaction
from django.contrib.auth.models import User
from django.utils.crypto import get_random_string
from django.utils import timezone
import json
from datetime import timedelta

class Client(models.Model):
    client_id = models.CharField(max_length=100, unique=True)
    client_secret = models.CharField(max_length=100)
    api_key = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=255)
    redirect_uris = models.TextField(help_text="One URI per line")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_redirect_uris(self):
        return self.redirect_uris.splitlines()
    
    def __str__(self):
        return self.name

class AuthorizationCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    @classmethod
    def create_code(cls, user, client):
        with transaction.atomic():
            # Delete any existing unused codes for this user-client pair
            cls.objects.filter(
                user=user,
                client=client
            ).delete()
            
            expires_at = timezone.now() + timedelta(minutes=10)
            
            return cls.objects.create(
                user=user,
                client=client,
                code=get_random_string(50),
                expires_at=expires_at
            )
    
    def __str__(self):
        return self.user.username + " - " + str(self.client.name)

class AccessToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    @classmethod
    def create_token(cls, user, client):
        
        with transaction.atomic():
            # Clean up old token
            cls.objects.filter(
                user=user,
                client=client
            ).delete()
            # Create new token
            expires_at = timezone.now() + timedelta(days=30)
            return cls.objects.create(
                user=user,
                client=client,
                token=get_random_string(50),
                expires_at=expires_at
            )
    
    def is_valid(self):
        return not self.is_expired()
    
    def is_expired(self):
        return timezone.now() >= self.expires_at
    
    def __str__(self):
        return self.user.username

class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    data = models.JSONField(default=dict)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.username