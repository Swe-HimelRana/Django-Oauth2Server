from django.contrib import admin
from .models import Client, AuthorizationCode, AccessToken, UserData
# Register your models here.

admin.site.register(Client)
admin.site.register(AuthorizationCode)
admin.site.register(AccessToken)
admin.site.register(UserData)