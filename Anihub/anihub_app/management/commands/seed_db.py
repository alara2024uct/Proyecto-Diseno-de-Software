from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from anihub_app.models import Post, Anime, Manga, Role
from anihub_app.services.anime_adapter import JikanAdapter

User = get_user_model()

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de prueba iniciales (Seed)'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING('Iniciando el proceso de Seeding...'))

        # =====================================================================
        # 1. CREACIÓN DE ROLES
        # =====================================================================
        roles_creados = {}
        for role_code, role_name in Role.ROLE_CHOICES:
            role_obj, created = Role.objects.get_or_create(
                name=role_code,
                defaults={"description": f"Rol de tipo {role_name}"}
            )
            roles_creados[role_code] = role_obj
            if created:
                self.stdout.write(self.style.SUCCESS(f"Rol creado: {role_name}"))

        # =====================================================================
        # 2. CREACIÓN DE USUARIOS DE PRUEBA (Manejo correcto de Propiedades y M2M)
        # =====================================================================
        usuarios_datos = [
            {"username": "otaku_introvertido", "password": "password123", "role": "USER", "secret": "TokenSecretoDePrueba1"},
            {"username": "nagatoro_fan", "password": "password123", "role": "USER", "secret": "TokenSecretoDePrueba2"},
            {"username": "subaru_sufrimientos", "password": "password123", "role": "MODERATOR", "secret": None},
        ]

        for u_data in usuarios_datos:
            if not User.objects.filter(username=u_data["username"]).exists():
                # Instanciamos el objeto de manera limpia sin pasarlo directamente al Manager
                nuevo_usuario = User(username=u_data["username"])
                nuevo_usuario.set_password(u_data["password"])
                
                # Asignamos el dato a través de la propiedad encriptada
                nuevo_usuario.sensitive_data = u_data["secret"]
                nuevo_usuario.save()  # Guardamos primero para generar el ID en BD
                
                # Asociamos el rol después de guardar (Obligatorio en relaciones ManyToMany)
                nuevo_usuario.roles.add(roles_creados[u_data["role"]])
                
                self.stdout.write(self.style.SUCCESS(f'Usuario creado: {u_data["username"]} con rol {u_data["role"]}'))
            else:
                self.stdout.write(f'El usuario {u_data["username"]} ya existía.')

        # =====================================================================
        # 3. CREACIÓN DE PUBLICACIONES (FORO ANÓNIMO)
        # =====================================================================
        posts_datos = [
            {"author_pseudonym": "LuffySolitario", "content": "Recomienden mangas cortos para leer un fin de semana lluvioso, por favor."},
            {"author_pseudonym": "SaitamaCalvo", "content": "El último episodio del anime de temporada tuvo una animación increíble. ¡10/10!"},
            {"author_pseudonym": "AsukaMejorWaifu", "content": "Opiniones honestas sobre el final de Evangelion aquí abajo."},
        ]

        for p_data in posts_datos:
            if not Post.objects.filter(content=p_data["content"]).exists():
                Post.objects.create(
                    author_pseudonym=p_data["author_pseudonym"],
                    content=p_data["content"]
                )
                self.stdout.write(self.style.SUCCESS(f'Post anónimo creado de: {p_data["author_pseudonym"]}'))

        # =====================================================================
        # 4. CREACIÓN DE ANIMES DE PRUEBA
        # =====================================================================
        animes_datos = [
            {
                "title": "Chainsaw Man",
                "synopsis": "Denji es un joven atrapado en la pobreza extrema que trabaja como cazador de demonios para saldar la deuda de su padre fallecido. Tras ser traicionado y asesinado, se fusiona con su perro demonio Pochita, reviviendo como 'Chainsaw Man', un híbrido con motosierras en sus extremidades.",
                "image_url": "https://images.justwatch.com/poster/301540306/s332/chainsaw-man",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            },
            {
                "title": "Frieren: Beyond Journey's End",
                "synopsis": "La maga elfa Frieren y sus valientes compañeros de aventura han derrotado al Rey Demonio, trayendo la paz al reino. Al ser una elfa, Frieren está destinada a ver cómo sus amigos envejecen y mueren. La historia sigue su viaje años después, buscando comprender mejor la naturaleza humana.",
                "image_url": "https://images.justwatch.com/poster/306786667/s332/frieren-beyond-journeys-end",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
            },
            {
                "title": "Cyberpunk: Edgerunners",
                "synopsis": "En una distopía futurista plagada de corrupción e implantes cibernéticos, un chico de la calle brillante pero descuidado intenta sobrevivir en Night City. Tras perderlo todo, decide convertirse en un 'edgerunner', un mercenario fuera de la ley también conocido como cyberpunk.",
                "image_url": "https://images.justwatch.com/poster/300445259/s332/cyberpunk-edgerunners",
                "video_url": "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4"
            }
        ]

        for a_data in animes_datos:
            obj, created = Anime.objects.get_or_create(
                title=a_data["title"],
                defaults={
                    "synopsis": a_data["synopsis"],
                    "image_url": a_data["image_url"],
                    "video_url": a_data["video_url"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Anime creado: {a_data["title"]}'))

        # =====================================================================
        # 5. CREACIÓN DE MANGAS DE PRUEBA
        # =====================================================================
        mangas_datos = [
            {
                "title": "Berserk",
                "synopsis": "Guts, un guerrero conocido como el 'Guerrero Negro', viaja por un mundo medieval oscuro y violento buscando venganza contra su antiguo mentor y amigo, Griffith, quien sacrificó a sus camaradas para obtener un poder divino casi absoluto.",
                "image_url": "https://images.justwatch.com/poster/8575005/s332/berserk",
                "pages_urls": "https://picsum.photos/id/10/800/1200,https://picsum.photos/id/11/800/1200,https://picsum.photos/id/12/800/1200"
            },
            {
                "title": "Oyasumi Punpun",
                "synopsis": "Una mirada profunda, realista y psicológica a la vida de Punpun Onodera, un niño representado visualmente como un pequeño pájaro amorfo. Acompañamos su crecimiento desde la primaria hasta sus veintes mientras lidia con el aislamiento y la depresión.",
                "image_url": "https://covers.openlibrary.org/b/id/12711559-L.jpg",
                "pages_urls": "https://picsum.photos/id/20/800/1200,https://picsum.photos/id/21/800/1200,https://picsum.photos/id/22/800/1200"
            },
            {
                "title": "Monster",
                "synopsis": "El brillante neurocirujano japonés Kenzo Tenma ejerce en Alemania occidental. Su vida cambia drásticamente al decidir salvar la vida de un niño herido de bala en lugar de la del alcalde de la ciudad. Años después, Tenma descubre que ese niño se ha convertido en un asesino serial.",
                "image_url": "https://images.justwatch.com/poster/302302324/s332/monster-2004",
                "pages_urls": "https://picsum.photos/id/30/800/1200,https://picsum.photos/id/31/800/1200,https://picsum.photos/id/32/800/1200"
            }
        ]

        for m_data in mangas_datos:
            obj, created = Manga.objects.get_or_create(
                title=m_data["title"],
                defaults={
                    "synopsis": m_data["synopsis"],
                    "image_url": m_data["image_url"],
                    "pages_urls": m_data["pages_urls"]
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Manga creado: {m_data["title"]}'))


        # =====================================================================
        # 6. INTEGRACIÓN DE MANGAS DESDE JIKAN API (VERSION CORREGIDA)
        # =====================================================================
        self.stdout.write(self.style.NOTICE('Importando catálogo de Jikan a la BD local...'))
        adapter = JikanAdapter()
        jikan_catalog = adapter.get_anime_catalog()

        # Usamos una clave más genérica o aseguramos el título exacto
        vinetas_personalizadas = {
            "Frieren: Beyond Journey's End": "https://i.postimg.cc/BZxdL1Tz/Captura-de-pantalla-2026-06-29-193102.png,https://i.postimg.cc/sDsbpDKy/Captura-de-pantalla-2026-06-29-194058.png,https://i.postimg.cc/9XGvRqPD/Captura-de-pantalla-2026-06-29-194232.png"
        }

        for item in jikan_catalog:
            titulo_jikan = item['title']
            
            # Buscar el manga en la BD usando búsqueda flexible (icontains)
            # Esto evita que una diferencia de una letra rompa la lógica
            manga_obj = Manga.objects.filter(title__icontains="Frieren").first() 
            
            # Si encontramos el manga (sea por título exacto o por el 'Frieren' que sabemos que existe)
            if manga_obj:
                paginas_nuevas = vinetas_personalizadas.get("Frieren: Beyond Journey's End")
                manga_obj.pages_urls = paginas_nuevas
                manga_obj.save()
                self.stdout.write(self.style.SUCCESS(f'Actualizado manualmente páginas para: {manga_obj.title}'))
            else:
                # Si no existe, lo creamos normalmente
                Manga.objects.get_or_create(
                    title=titulo_jikan,
                    defaults={
                        "synopsis": item.get('synopsis', ''),
                        "image_url": item.get('image_url', ''),
                        "pages_urls": "https://picsum.photos/id/1/800/1200"
                    }
                )
        
        
        self.stdout.write(self.style.SUCCESS('¡Base de datos poblada con éxito! 🚀'))