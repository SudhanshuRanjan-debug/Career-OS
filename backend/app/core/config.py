"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables / .env file.
"""

from typing import List, Optional, Union
from urllib.parse import urlsplit
from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

KNOWN_INSECURE_SECRETS = {
    "change_me_in_production_use_random_32_bytes",
    "prod_super_secret_jwt_key_at_least_32_chars_long",
    "insecure_default_dev_secret_key_minimum_32_chars_long_12345",
    "replace_with_a_random_development_secret",
    "generate_a_strong_random_secret_key_at_least_64_characters_long",
    "secret",
    "changeme",
    "supersecret",
    "defaultsecret",
}

KNOWN_INSECURE_PASSWORDS = {
    "postgres",
    "password",
    "admin",
    "root",
    "123456",
    "12345678",
    "replace_with_local_database_password",
    "generate_a_cryptographically_secure_password_here",
    "changeme",
}


def _extract_db_password(database_url: str) -> Optional[str]:
    """Safely extract password component from database URL."""
    try:
        parsed = urlsplit(database_url)
        return parsed.password
    except Exception:
        return None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ---------------------------------------------------------------------------
    # Application
    # ---------------------------------------------------------------------------
    APP_ENV: str = Field("development", validation_alias=AliasChoices("APP_ENV", "ENVIRONMENT"))
    DEBUG: Optional[bool] = Field(None, validation_alias=AliasChoices("DEBUG"))
    ENABLE_API_DOCS: bool = Field(False, validation_alias=AliasChoices("ENABLE_API_DOCS", "ENABLE_DOCS"))
    APP_NAME: str = "Career Platform API"
    APP_VERSION: str = "1.0.0"

    ALLOWED_ORIGINS: Union[List[str], str] = Field(
        ["http://localhost:5173", "http://localhost:3000", "http://localhost:80"],
        validation_alias=AliasChoices("ALLOWED_ORIGINS", "CORS_ORIGINS", "BACKEND_CORS_ORIGINS"),
    )
    ALLOWED_HOSTS: Union[List[str], str] = Field(
        ["localhost", "127.0.0.1", "testserver"],
        validation_alias=AliasChoices("ALLOWED_HOSTS"),
    )

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod")

    @property
    def docs_enabled(self) -> bool:
        if self.is_production:
            return self.ENABLE_API_DOCS
        return bool(self.DEBUG or self.ENABLE_API_DOCS)

    @field_validator("ALLOWED_ORIGINS", "ALLOWED_HOSTS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # ---------------------------------------------------------------------------
    # Database
    # ---------------------------------------------------------------------------
    POSTGRES_PASSWORD: Optional[str] = Field(
        None,
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "DB_PASSWORD"),
    )
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/career_platform"

    # ---------------------------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------------------------
    SECRET_KEY: str = Field(
        "CHANGE_ME_IN_PRODUCTION_USE_RANDOM_32_BYTES",
        validation_alias=AliasChoices("SECRET_KEY", "JWT_SECRET"),
    )
    ALGORITHM: str = Field("HS256", validation_alias=AliasChoices("ALGORITHM", "JWT_ALGORITHM"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    BCRYPT_ROUNDS: int = 12
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_PATH: str = "/api/v1/auth"

    @property
    def COOKIE_SECURE(self) -> bool:
        return self.is_production

    @property
    def COOKIE_SAMESITE(self) -> str:
        return "strict" if self.is_production else "lax"

    # ---------------------------------------------------------------------------
    # File Storage
    # ---------------------------------------------------------------------------
    STORAGE_BACKEND: str = Field("local", validation_alias=AliasChoices("STORAGE_BACKEND", "STORAGE_PROVIDER"))
    STORAGE_LOCAL_PATH: str = Field("./storage/private", validation_alias=AliasChoices("STORAGE_LOCAL_PATH", "STORAGE_LOCAL_ROOT"))

    # Azure Blob Storage (production)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = Field(
        "career-platform-files",
        validation_alias=AliasChoices("AZURE_STORAGE_CONTAINER", "AZURE_STORAGE_CONTAINER_NAME"),
    )

    @property
    def STORAGE_PROVIDER(self) -> str:
        return self.STORAGE_BACKEND

    @property
    def STORAGE_LOCAL_ROOT(self) -> str:
        return self.STORAGE_LOCAL_PATH

    # File upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
    ALLOWED_RESUME_MIME_TYPES: List[str] = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    # ---------------------------------------------------------------------------
    # Authentication Rate Limiting
    # ---------------------------------------------------------------------------
    RATE_LIMIT_ENABLED: bool = True

    # Login endpoint limits
    RATE_LIMIT_LOGIN_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_LOGIN_WINDOW_SECONDS: int = 60
    RATE_LIMIT_LOGIN_IP_MAX_ATTEMPTS: int = 50
    RATE_LIMIT_LOGIN_IP_WINDOW_SECONDS: int = 60

    # Registration endpoint limits
    RATE_LIMIT_REGISTER_MAX_ATTEMPTS: int = 15
    RATE_LIMIT_REGISTER_WINDOW_SECONDS: int = 60

    # Refresh token endpoint limits
    RATE_LIMIT_REFRESH_MAX_ATTEMPTS: int = 30
    RATE_LIMIT_REFRESH_WINDOW_SECONDS: int = 60

    # Forgot password endpoint limits
    RATE_LIMIT_FORGOT_PASSWORD_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_FORGOT_PASSWORD_WINDOW_SECONDS: int = 900  # 15 minutes
    RATE_LIMIT_FORGOT_PASSWORD_IP_MAX_ATTEMPTS: int = 30
    RATE_LIMIT_FORGOT_PASSWORD_IP_WINDOW_SECONDS: int = 900

    # Reset password endpoint limits
    RATE_LIMIT_RESET_PASSWORD_MAX_ATTEMPTS: int = 10
    RATE_LIMIT_RESET_PASSWORD_WINDOW_SECONDS: int = 600  # 10 minutes

    # Change password endpoint limits
    RATE_LIMIT_CHANGE_PASSWORD_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_CHANGE_PASSWORD_WINDOW_SECONDS: int = 300  # 5 minutes

    # ---------------------------------------------------------------------------
    # Email (future — Stage 9)
    # ---------------------------------------------------------------------------
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@careerplatform.example.com"

    # ---------------------------------------------------------------------------
    # Production Security Validations
    # ---------------------------------------------------------------------------
    @model_validator(mode="after")
    def validate_environment_and_security(self) -> "Settings":
        # Resolve default for DEBUG if unset
        if self.DEBUG is None:
            self.DEBUG = not self.is_production
        elif self.is_production and self.DEBUG:
            raise ValueError(
                "Production startup rejected: DEBUG mode cannot be enabled when "
                "APP_ENV/ENVIRONMENT is 'production'. Set DEBUG=false."
            )

        if self.is_production:
            # 1. Validate SECRET_KEY
            secret = (self.SECRET_KEY or "").strip()
            secret_lower = secret.lower()
            if not secret:
                raise ValueError("Production startup rejected: SECRET_KEY is missing or empty.")
            if len(secret) < 32:
                raise ValueError(
                    f"Production startup rejected: SECRET_KEY is too short ({len(secret)} characters). "
                    "Must be at least 32 characters long."
                )
            if secret_lower in KNOWN_INSECURE_SECRETS or any(
                ph in secret_lower for ph in ["change_me", "replace_with", "generate_a_strong", "super_secret"]
            ):
                raise ValueError(
                    "Production startup rejected: Insecure or default placeholder SECRET_KEY detected. "
                    "You must configure a strong, random production secret key (e.g. openssl rand -hex 32)."
                )

            # 2. Validate Database Password
            db_passwords: list[str] = []
            if self.POSTGRES_PASSWORD:
                db_passwords.append(self.POSTGRES_PASSWORD.strip())

            extracted_pwd = _extract_db_password(self.DATABASE_URL)
            if extracted_pwd:
                db_passwords.append(extracted_pwd.strip())

            is_postgres = "postgres" in (self.DATABASE_URL or "").lower()
            if is_postgres and not db_passwords:
                raise ValueError(
                    "Production startup rejected: Database password is required in production. "
                    "Set POSTGRES_PASSWORD or provide a password in DATABASE_URL."
                )

            for pwd in db_passwords:
                pwd_lower = pwd.lower()
                if pwd_lower in KNOWN_INSECURE_PASSWORDS or any(
                    ph in pwd_lower for ph in ["replace_with", "generate_a_crypto", "change_me"]
                ):
                    raise ValueError(
                        f"Production startup rejected: Insecure or default database password '{pwd}' detected. "
                        "You must configure a secure, unique password in POSTGRES_PASSWORD and DATABASE_URL."
                    )

            # 3. Validate ALLOWED_HOSTS (No wildcards permitted)
            if not self.ALLOWED_HOSTS:
                raise ValueError(
                    "Production startup rejected: ALLOWED_HOSTS must not be empty in production."
                )
            if any("*" in host for host in self.ALLOWED_HOSTS):
                raise ValueError(
                    "Production startup rejected: ALLOWED_HOSTS cannot contain wildcard '*' in production. "
                    "Specify explicit domain names or hostnames."
                )

        return self


settings = Settings()
