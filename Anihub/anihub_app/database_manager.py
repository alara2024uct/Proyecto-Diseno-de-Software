import threading
import psycopg2
from django.conf import settings

class DatabaseConnection:
    """
    Implementación Thread-Safe del patrón Singleton para la conexión a PostgreSQL.
    Garantiza que solo exista una instancia de este gestor de recursos en toda la app.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DatabaseConnection, cls).__new__(cls)
                cls._instance._initialize_connection()
        return cls._instance

    def _initialize_connection(self):
        """Inicializa la conexión real a PostgreSQL usando las variables de entorno de Django"""
        db_settings = settings.DATABASES['default']
        try:
            self.connection = psycopg2.connect(
                dbname=db_settings['NAME'],
                user=db_settings['USER'],
                password=db_settings['PASSWORD'],
                host=db_settings['HOST'],
                port=db_settings['PORT']
            )
            self.connection.autocommit = True
        except psycopg2.Error as e:
            # Aquí idealmente se integraría un sistema de logs
            print(f"Error al conectar a la base de datos a través del Singleton: {e}")
            self.connection = None

    def get_connection(self):
        return self.connection

    def close_connection(self):
        if self.connection is not None:
            self.connection.close()
            self.connection = None
