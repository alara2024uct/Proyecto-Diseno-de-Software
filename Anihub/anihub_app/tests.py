import time
from unittest.mock import patch, MagicMock
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model, get_user
from anihub_app.auth import AuthTokenService
from anihub_app.models import Manga, Anime
from django.db import IntegrityError
from anihub_app.services.anime_adapter import JikanAdapter
from anihub_app.views import CatalogView, ForumView
import json
from anihub_app.database_manager import DatabaseConnection

User = get_user_model()

class TestAuthTokenService(TestCase):
    def setUp(self):
        self.token_service = AuthTokenService()
        self.user_id = 42

    def test_generate_and_validate_token(self):
        # Generate token
        token = self.token_service.generate_token(self.user_id)
        self.assertIsNotNone(token)
        self.assertIsInstance(token, str)

        # Validate token
        payload = self.token_service.validate_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("user_id"), self.user_id)
        self.assertGreater(payload.get("exp"), time.time())

    def test_expired_token(self):
        # Generate a token with a negative expiration (expired in the past)
        token = self.token_service.generate_token(self.user_id, expiration_seconds=-10)
        self.assertIsNotNone(token)

        # Validate token should return None
        payload = self.token_service.validate_token(token)
        self.assertIsNone(payload)

    def test_invalid_token_format(self):
        # Validate random string
        payload = self.token_service.validate_token("invalid_token_string")
        self.assertIsNone(payload)

        # Validate empty string
        payload = self.token_service.validate_token("")
        self.assertIsNone(payload)

    def test_tampered_token(self):
        # Generate a valid token
        token = self.token_service.generate_token(self.user_id)
        
        # Tamper it by replacing some characters
        if ":" in token:
            iv, ct = token.split(":")
            # Alter the ciphertext
            tampered_ct = ct[:-2] + "AA"
            tampered_token = f"{iv}:{tampered_ct}"
        else:
            tampered_token = token[:-2] + "AA"

        payload = self.token_service.validate_token(tampered_token)
        self.assertIsNone(payload)


class TestTokenRequiredDecorator(TestCase):
    def setUp(self):
        self.token_service = AuthTokenService()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpassword123",
            email="testuser@example.com"
        )
        self.token = self.token_service.generate_token(self.user.id)
        self.url = reverse("api_catalog")

    @patch("anihub_app.views.JikanAdapter.get_anime_catalog")
    def test_valid_token(self, mock_get_anime_catalog):
        mock_get_anime_catalog.return_value = [{"title": "Death Note"}]
        
        headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        response = self.client.get(self.url, **headers)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("catalog", data)
        self.assertEqual(data["catalog"], [{"title": "Death Note"}])
        mock_get_anime_catalog.assert_called_once()

    def test_missing_auth_header(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Token missing or invalid"})

    def test_malformed_auth_header(self):
        # Header present but does not start with Bearer
        headers = {"HTTP_AUTHORIZATION": f"Token {self.token}"}
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Token missing or invalid"})

        # Header has Bearer but lacks token
        headers = {"HTTP_AUTHORIZATION": "Bearer"}
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Token missing or invalid"})

    def test_invalid_token(self):
        headers = {"HTTP_AUTHORIZATION": "Bearer invalidtoken123"}
        response = self.client.get(self.url, **headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json(), {"error": "Invalid or expired token"})


class TestLoginView(TestCase):
    def setUp(self):
        self.login_url = reverse("login")
        self.username = "testuser"
        self.password = "securepassword123"
        self.user = User.objects.create_user(
            username=self.username,
            password=self.password,
            email="testuser@example.com"
        )

    def test_login_get(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/login.html")
        self.assertIn("form", response.context)

    def test_login_post_success(self):
        # Log in with correct credentials
        response = self.client.post(self.login_url, {
            "username": self.username,
            "password": self.password
        })
        # Check redirection to 'home'
        self.assertRedirects(response, reverse("home"))
        
        # Check if the user is authenticated in the session
        user = get_user(self.client)
        self.assertTrue(user.is_authenticated)
        self.assertEqual(user.username, self.username)

    def test_login_post_failure(self):
        # Log in with incorrect credentials
        response = self.client.post(self.login_url, {
            "username": self.username,
            "password": "wrongpassword"
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/login.html")
        self.assertIn("form", response.context)
        
        # Check that the form in context has validation errors
        form = response.context["form"]
        self.assertFalse(form.is_valid())
        
        # Check that the user is not authenticated in the session
        user = get_user(self.client)
        self.assertFalse(user.is_authenticated)


class TestCatalogView(TestCase):
    def setUp(self):
        self.token_service = AuthTokenService()
        self.user = User.objects.create_user(
            username="cataloguser",
            password="testpassword123",
            email="cataloguser@example.com"
        )
        self.token = self.token_service.generate_token(self.user.id)
        self.url = reverse("api_catalog")
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}

    @patch("anihub_app.views.JikanAdapter.get_anime_catalog")
    def test_catalog_view_success(self, mock_get_anime_catalog):
        mock_catalog = [
            {"title": "Chainsaw Man", "synopsis": "Cool anime", "image_url": "http://example.com/csm.jpg"},
            {"title": "Frieren", "synopsis": "Elf adventure", "image_url": "http://example.com/frieren.jpg"}
        ]
        mock_get_anime_catalog.return_value = mock_catalog
        
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["catalog"], mock_catalog)
        mock_get_anime_catalog.assert_called_once()

    @patch("anihub_app.views.JikanAdapter.get_anime_catalog")
    def test_catalog_view_empty_list(self, mock_get_anime_catalog):
        mock_get_anime_catalog.return_value = []
        
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["catalog"], [])
        mock_get_anime_catalog.assert_called_once()

    def test_catalog_view_unauthenticated(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class TestJikanAdapter(TestCase):
    def setUp(self):
        self.adapter = JikanAdapter()

    @patch("requests.get")
    def test_get_anime_catalog_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "title": "Chainsaw Man",
                    "synopsis": "Cool anime",
                    "images": {"jpg": {"image_url": "http://example.com/csm.jpg"}}
                }
            ]
        }
        
        catalog = self.adapter.get_anime_catalog()
        self.assertEqual(len(catalog), 1)
        self.assertEqual(catalog[0]["title"], "Chainsaw Man")
        self.assertEqual(catalog[0]["synopsis"], "Cool anime")
        self.assertEqual(catalog[0]["image_url"], "http://example.com/csm.jpg")
        mock_get.assert_called_once_with(JikanAdapter.BASE_URL, timeout=10)

    @patch("requests.get")
    def test_get_anime_catalog_failure(self, mock_get):
        from requests.exceptions import RequestException
        mock_get.side_effect = RequestException("Connection timeout")
        
        catalog = self.adapter.get_anime_catalog()
        self.assertEqual(catalog, [])
        mock_get.assert_called_once_with(JikanAdapter.BASE_URL, timeout=10)


class TestWatchMangaView(TestCase):
    def setUp(self):
        self.manga = Manga.objects.create(
            title="Berserk",
            synopsis="Epic dark fantasy",
            image_url="http://example.com/berserk.jpg",
            pages_urls="http://example.com/page1.jpg,http://example.com/page2.jpg"
        )
        self.valid_url = reverse("watch_manga", kwargs={"manga_id": self.manga.id})
        self.invalid_url = reverse("watch_manga", kwargs={"manga_id": 9999})

    def test_watch_manga_view_success(self):
        response = self.client.get(self.valid_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/watch_manga.html")
        
        self.assertIn("manga", response.context)
        self.assertEqual(response.context["manga"], self.manga)
        self.assertIn("paginas", response.context)
        self.assertEqual(response.context["paginas"], ["http://example.com/page1.jpg", "http://example.com/page2.jpg"])

    def test_watch_manga_view_not_found(self):
        response = self.client.get(self.invalid_url)
        self.assertEqual(response.status_code, 404)

    def test_watch_manga_view_empty_pages(self):
        empty_manga = Manga.objects.create(
            title="No Pages Manga",
            synopsis="A manga with no pages",
            image_url="http://example.com/nopages.jpg",
            pages_urls=""
        )
        url = reverse("watch_manga", kwargs={"manga_id": empty_manga.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["paginas"], [])


class TestAnimeModel(TestCase):
    def test_anime_creation(self):
        anime = Anime.objects.create(
            title="Chainsaw Man",
            synopsis="Denji is a boy with chainsaws",
            image_url="http://example.com/csm.jpg",
            video_url="http://example.com/csm.mp4"
        )
        self.assertEqual(anime.title, "Chainsaw Man")
        self.assertEqual(anime.synopsis, "Denji is a boy with chainsaws")
        self.assertEqual(anime.image_url, "http://example.com/csm.jpg")
        self.assertEqual(anime.video_url, "http://example.com/csm.mp4")
        self.assertEqual(str(anime), "Chainsaw Man")

    def test_anime_title_uniqueness(self):
        Anime.objects.create(
            title="Duplicate Title",
            synopsis="Synopsis 1",
            image_url="http://example.com/img1.jpg",
            video_url="http://example.com/video1.mp4"
        )
        with self.assertRaises(IntegrityError):
            Anime.objects.create(
                title="Duplicate Title",
                synopsis="Synopsis 2",
                image_url="http://example.com/img2.jpg",
                video_url="http://example.com/video2.mp4"
            )


class TestMangaModel(TestCase):
    def test_manga_creation(self):
        manga = Manga.objects.create(
            title="Berserk",
            synopsis="Guts revenge story",
            image_url="http://example.com/berserk.jpg",
            pages_urls="http://example.com/p1.jpg,http://example.com/p2.jpg"
        )
        self.assertEqual(manga.title, "Berserk")
        self.assertEqual(manga.synopsis, "Guts revenge story")
        self.assertEqual(manga.image_url, "http://example.com/berserk.jpg")
        self.assertEqual(manga.pages_urls, "http://example.com/p1.jpg,http://example.com/p2.jpg")
        self.assertEqual(str(manga), "Berserk")

    def test_manga_title_uniqueness(self):
        Manga.objects.create(
            title="Duplicate Title",
            synopsis="Synopsis 1",
            image_url="http://example.com/img1.jpg",
            pages_urls="http://example.com/p1.jpg"
        )
        with self.assertRaises(IntegrityError):
            Manga.objects.create(
                title="Duplicate Title",
                synopsis="Synopsis 2",
                image_url="http://example.com/img2.jpg",
                pages_urls="http://example.com/p2.jpg"
            )


class TestFrontendViews(TestCase):
    def test_home_view(self):
        url = reverse("home")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/home.html")

    def test_movies_view(self):
        url = reverse("movies")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "anihub_app/movies.html")


class TestSearchView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="searchuser",
            password="testpassword123",
            email="searchuser@example.com"
        )
        self.token_service = AuthTokenService()
        self.token = self.token_service.generate_token(self.user.id)
        self.headers = {"HTTP_AUTHORIZATION": f"Bearer {self.token}"}
        
        self.anime1 = Anime.objects.create(
            title="Chainsaw Man",
            synopsis="A cool action anime with devils.",
            image_url="http://example.com/csm.jpg",
            video_url="http://example.com/csm.mp4"
        )
        self.anime2 = Anime.objects.create(
            title="Frieren",
            synopsis="Elf adventure after the demon king is defeated.",
            image_url="http://example.com/frieren.jpg",
            video_url="http://example.com/frieren.mp4"
        )
        self.manga1 = Manga.objects.create(
            title="Chainsaw Man Manga",
            synopsis="The original manga by Tatsuki Fujimoto.",
            image_url="http://example.com/csm_manga.jpg",
            pages_urls="http://example.com/p1.jpg,http://example.com/p2.jpg"
        )
        self.manga2 = Manga.objects.create(
            title="Monster",
            synopsis="A psychological thriller about a doctor.",
            image_url="http://example.com/monster.jpg",
            pages_urls="http://example.com/p1.jpg"
        )
        self.url = reverse("api_search")

    def test_search_success(self):
        # Search for "chainsaw"
        response = self.client.get(f"{self.url}?q=chainsaw", **self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn("anime", data)
        self.assertIn("manga", data)
        
        # Verify Anime results
        anime_titles = [a["title"] for a in data["anime"]]
        self.assertIn("Chainsaw Man", anime_titles)
        self.assertNotIn("Frieren", anime_titles)
        
        # Verify Manga results
        manga_titles = [m["title"] for m in data["manga"]]
        self.assertIn("Chainsaw Man Manga", manga_titles)
        self.assertNotIn("Monster", manga_titles)

    def test_search_case_insensitive(self):
        # Search with uppercase "FRIEREN"
        response = self.client.get(f"{self.url}?q=FRIEREN", **self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        anime_titles = [a["title"] for a in data["anime"]]
        self.assertIn("Frieren", anime_titles)
        self.assertEqual(len(data["manga"]), 0)

    def test_search_no_query(self):
        # Request search without 'q' parameter
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["anime"], [])
        self.assertEqual(data["manga"], [])

        # Request search with empty 'q' parameter
        response = self.client.get(f"{self.url}?q=", **self.headers)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(data["anime"], [])
        self.assertEqual(data["manga"], [])

    def test_search_unauthenticated(self):
        # Request search without Bearer token
        response = self.client.get(f"{self.url}?q=chainsaw")
        self.assertEqual(response.status_code, 401)



class TestViews(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_catalog_view_get(self):
        # Mock del provider para no llamar a la API real
        mock_provider = MagicMock()
        mock_provider.get_anime_catalog.return_value = [{'title': 'Naruto'}]
        
        request = self.factory.get('/api/catalog/')
        # Pasamos el mock al constructor de la vista
        view = CatalogView(provider=mock_provider)
        response = view.get(request)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('catalog', json.loads(response.content))

    def test_forum_view_post_success(self):
        mock_anonymizer = MagicMock()
        mock_anonymizer.generate_pseudonym.return_value = "Saiyajin_Sombra"
        
        data = {'content': 'Hola, mundo'}
        request = self.factory.post('/forum/', data=json.dumps(data), content_type='application/json')
        
        view = ForumView(anonymizer=mock_anonymizer)
        response = view.post(request)
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json.loads(response.content)['author'], "Saiyajin_Sombra")

    def test_forum_view_post_empty_content(self):
        request = self.factory.post('/forum/', data=json.dumps({}), content_type='application/json')
        view = ForumView()
        response = view.post(request)
        self.assertEqual(response.status_code, 400)



class TestDatabaseConnection(TestCase):
    def setUp(self):
        # Limpiamos el singleton antes de cada test
        DatabaseConnection._instance = None

    @patch('psycopg2.connect')
    def test_singleton_pattern(self, mock_connect):
        # Instanciamos dos veces
        db1 = DatabaseConnection()
        db2 = DatabaseConnection()
        
        # Deben ser el mismo objeto en memoria
        self.assertEqual(id(db1), id(db2))
        # El método connect solo debe llamarse una vez, incluso tras doble instanciación
        self.assertEqual(mock_connect.call_count, 1)

    @patch('psycopg2.connect')
    def test_connection_failure(self, mock_connect):
        # Simulamos un error de conexión
        mock_connect.side_effect = Exception("DB Connection Error")
        db = DatabaseConnection()
        self.assertIsNone(db.get_connection())