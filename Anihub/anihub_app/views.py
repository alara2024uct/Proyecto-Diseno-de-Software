import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.shortcuts import render, redirect

from .auth import token_required
from .services.anime_adapter import AnimeProvider, JikanAdapter
from .services.anonymizer import AnonymizerService
from .models import Post, CustomUser
from .forms import LoginForm
from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import RegisterSerializer


@method_decorator(token_required, name='dispatch')
class CatalogView(View):
    """FR-1: Vista del catálogo usando Inyección de Dependencias (DIP)"""
    
    def __init__(self, provider: AnimeProvider = None, **kwargs):
        super().__init__(**kwargs)
        self.provider = provider or JikanAdapter()

    def get(self, request):
        catalog = self.provider.get_anime_catalog()
        return JsonResponse({"catalog": catalog}, status=200)

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(token_required, name='dispatch')
class ForumView(View):
    """FR-2: Vista del foro con anonimización automática"""
    
    def __init__(self, anonymizer: AnonymizerService = None, **kwargs):
        super().__init__(**kwargs)
        self.anonymizer = anonymizer or AnonymizerService()

    def post(self, request):
        try:
            data = json.loads(request.body)
            content = data.get('content')
            
            if not content:
                return JsonResponse({"error": "Content is required"}, status=400)

            pseudonym = self.anonymizer.generate_pseudonym()
            
            post = Post.objects.create(
                author_pseudonym=pseudonym,
                content=content
            )
            
            return JsonResponse({
                "message": "Post created successfully",
                "post_id": post.id,
                "author": pseudonym
            }, status=201)
            
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)


# =====================================================================
# VISTAS PARA EL RENDERIZADO DE PLANTILLAS FRONTEND (HTML)
# =====================================================================

def login_view(request):
    return render(request, 'anihub_app/login.html')

def register_view(request):
    return render(request, 'anihub_app/register.html')

class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Usuario creado con éxito"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def home_view(request):
    """Catálogo principal de mangas"""
    return render(request, 'anihub_app/home.html')

def movies_view(request):
    """Sección de videos y anime"""
    return render(request, 'anihub_app/movies.html')

def watch_manga_view(request):
    """Lector individual para tomos de manga"""
    return render(request, 'anihub_app/watch_manga.html')

def forum_view(request):
    """Vista pública del foro comunitario"""
    return render(request, 'anihub_app/forum.html')

def profile_view(request):
    """Perfil del usuario autenticado"""
    return render(request, 'anihub_app/profile.html')

def chat_view(request):
    """Sala de chat privado"""
    return render(request, 'anihub_app/chat.html')

def favorites_view(request):
    """Lista de favoritos guardados"""
    return render(request, 'anihub_app/favorites.html')

def quiz_view(request):
    """Sección interactiva de trivia y quizzes"""
    return render(request, 'anihub_app/quiz.html')

def news_view(request):
    """Noticias de actualidad sobre anime"""
    return render(request, 'anihub_app/news.html')
