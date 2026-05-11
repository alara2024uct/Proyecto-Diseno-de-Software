from abc import ABC, abstractmethod
import requests

class AnimeProvider(ABC):
    """Abstracción para el proveedor de Anime (Dependency Inversion)"""
    @abstractmethod
    def get_anime_catalog(self) -> list:
        pass

class JikanAdapter(AnimeProvider):
    """Adaptador concreto para la API de Jikan (MyAnimeList)"""
    BASE_URL = "https://api.jikan.moe/v4/top/anime"

    def get_anime_catalog(self) -> list:
        try:
            response = requests.get(self.BASE_URL, timeout=10)
            response.raise_for_status()
            data = response.json().get('data', [])
            
            # Normalización al formato interno
            catalog = []
            for anime in data[:10]: # Limitamos a 10 para el ejemplo
                catalog.append({
                    "title": anime.get("title"),
                    "synopsis": anime.get("synopsis", "Sin sinopsis disponible."),
                    "image_url": anime.get("images", {}).get("jpg", {}).get("image_url", "")
                })
            return catalog
        except requests.RequestException as e:
            print(f"Error fetching from Jikan API: {e}")
            return []
