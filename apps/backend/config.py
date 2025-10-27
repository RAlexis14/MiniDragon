import os

class Settings:
    """12-factor style config."""
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
    DRAGON_API_BASE = os.getenv("DRAGON_API_BASE", "https://dragonball-api.com/api/characters")
    DB_FILE = os.getenv("DB_FILE", "/data/minidragon.sqlite")
