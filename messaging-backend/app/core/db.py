from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongo_user: str
    mongo_password: str
    mongo_host: str
    mongo_port: int
    mongo_db_name: str

    @property
    def mongo_uri(self) -> str:
        # authSource obligatoire : l'utilisateur est créé dans mongo_db_name, pas dans admin
        user = quote_plus(self.mongo_user)
        password = quote_plus(self.mongo_password)
        return (
            f"mongodb://{user}:{password}@{self.mongo_host}:{self.mongo_port}"
            f"/?authSource={quote_plus(self.mongo_db_name)}"
        )

@lru_cache
def get_settings():
    return Settings()