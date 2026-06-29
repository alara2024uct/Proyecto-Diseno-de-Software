"""
URL configuration for anihub_project project.
"""
from django.contrib import admin
from django.urls import path
from anihub_app import views  # Importación limpia y directa de las vistas de la app
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import RegisterView

urlpatterns = [    
    # -----------------------------------------------------------------
    # RUTAS DE INTERFAZ (FRONTEND MODULAR)
    # -----------------------------------------------------------------
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('home/', views.home_view, name='home'),
    path('movies/', views.movies_view, name='movies'),
    path('manga/read/', views.watch_manga_view, name='watch_manga'),
    path('forum/', views.forum_view, name='forum'),
    
    # Nuevas rutas añadidas para el menú lateral (Sidebar)
    path('profile/', views.profile_view, name='profile'),
    path('chat/', views.chat_view, name='chat'),
    path('favorites/', views.favorites_view, name='favorites'),
    path('quiz/', views.quiz_view, name='quiz'),
    path('news/', views.news_view, name='news'),

    # -----------------------------------------------------------------
    # ENDPOINTS DE API REST (BACKEND LOGIC)
    # -----------------------------------------------------------------
    path('api/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/register/', RegisterView.as_view(), name='register_api'),
    path('api/catalog/', views.CatalogView.as_view(), name='api_catalog'),
    path('api/forum/post/', views.ForumView.as_view(), name='api_forum_post'),
]
