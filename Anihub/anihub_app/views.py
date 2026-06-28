import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

from .auth import token_required
from .services.anime_adapter import AnimeProvider, JikanAdapter
from .services.anonymizer import AnonymizerService
from .models import Post

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