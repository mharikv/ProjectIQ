from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    secret_key: str = "dev-secret-key-change-in-production"
    database_url: str = "sqlite:///./manufacturing_pm.db"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    serve_frontend: bool = False
    static_dir: str = "static"
    port: int = 8000

    class Config:
        env_file = ".env"


settings = Settings()

