from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Post, Anime, Manga

admin.site.register(CustomUser, UserAdmin)
admin.site.register(Post)
admin.site.register(Anime)
admin.site.register(Manga)
