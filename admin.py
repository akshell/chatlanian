# (c) 2011 by Anton Korenyushkin

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

UserAdmin.list_display = ('username', 'email', 'date_joined', 'last_login')

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
