# %%
from pydantic_settings import BaseSettings

# class CustomBaseSettings(BaseSettings):
#     model_config = SettingsConfigDict(
#         env_file=".env", env_file_encoding="utf-8", extra="ignore"
#     )


class Config(BaseSettings):
    DATABASE_ASYNC_URL: str = (
        "postgresql+asyncpg://postgres:postgres@postgres:5432/mydb"
    )

    DATABASE_POOL_SIZE: int = 16
    DATABASE_POOL_TTL: int = 60 * 20  # 20 minutes
    DATABASE_POOL_PRE_PING: bool = True
    EMBED_SERVER_URL: str = "http://localhost:8005"
    LANCDEDB_PATH: str = ".lancedb"
    LANCEDB_TABLE_NAME: str = "images"
    IMAGE_DIR: str = "imgs"


settings = Config()

# %%
