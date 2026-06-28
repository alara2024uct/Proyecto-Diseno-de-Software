import random

class AnonymizerService:
    """Servicio encargado exclusivamente de generar identidades anónimas."""
    
    RACES = "Shinobi", "Saiyajin", "Hollow", "Hunter", "Alchemist", "Cyborg", "Titan", "Hokage", "Ghoul", "Proxy", "StandUser"
    ADJECTIVES = "Sombra", "Espectro", "Zenith", "Void", "Cipher", "Protocol", "Nexus", "Glitch", "Umbra", "Ronin", "Rebel"

    def generate_pseudonym(self) -> str:
        char = random.choice(self.RACES)
        adj = random.choice(self.ADJECTIVES)
        return f"{char}_{adj}"