"""Application configuration management using Pydantic Settings."""

from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """Application general settings."""

    name: str = Field(default="AutoScholar", alias="APP_NAME")
    version: str = Field(default="0.1.0", alias="APP_VERSION")
    env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="APP_DEBUG")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    host: str = Field(default="localhost", alias="DATABASE_HOST")
    port: int = Field(default=5432, alias="DATABASE_PORT")
    name: str = Field(default="autoscholar", alias="DATABASE_NAME")
    user: str = Field(default="autoscholar_user", alias="DATABASE_USER")
    password: str = Field(default="", alias="DATABASE_PASSWORD")
    pool_size: int = Field(default=10, alias="DATABASE_POOL_SIZE")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @property
    def url(self) -> str:
        """Generate database URL."""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def sync_url(self) -> str:
        """Generate sync database URL for Alembic."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class LLMProviderSettings(BaseSettings):
    """LLM provider specific settings."""

    api_key: str = ""
    api_base: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 4000
    timeout: int = 60

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class LLMSettings(BaseSettings):
    """LLM configuration settings."""

    default_provider: str = Field(default="openai", alias="LLM_DEFAULT_PROVIDER")
    fallback_provider: str = Field(default="qwen", alias="LLM_FALLBACK_PROVIDER")

    # OpenAI
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_api_base: str = Field(
        default="https://api.openai.com/v1", alias="OPENAI_API_BASE"
    )
    openai_model: str = Field(default="gpt-4", alias="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.7, alias="OPENAI_TEMPERATURE")
    openai_max_tokens: int = Field(default=4000, alias="OPENAI_MAX_TOKENS")

    # Qwen
    qwen_api_key: str = Field(default="", alias="QWEN_API_KEY")
    qwen_api_base: str = Field(
        default="https://dashscope.aliyuncs.com/api/v1", alias="QWEN_API_BASE"
    )
    qwen_model: str = Field(default="qwen-max", alias="QWEN_MODEL")
    qwen_temperature: float = Field(default=0.7, alias="QWEN_TEMPERATURE")
    qwen_max_tokens: int = Field(default=4000, alias="QWEN_MAX_TOKENS")

    # Zhipu
    zhipu_api_key: str = Field(default="", alias="ZHIPU_API_KEY")
    zhipu_api_base: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4", alias="ZHIPU_API_BASE"
    )
    zhipu_model: str = Field(default="glm-4", alias="ZHIPU_MODEL")
    zhipu_temperature: float = Field(default=0.7, alias="ZHIPU_TEMPERATURE")
    zhipu_max_tokens: int = Field(default=4000, alias="ZHIPU_MAX_TOKENS")

    # Kimi
    kimi_api_key: str = Field(default="", alias="KIMI_API_KEY")
    kimi_api_base: str = Field(
        default="https://api.moonshot.cn/v1", alias="KIMI_API_BASE"
    )
    kimi_model: str = Field(default="moonshot-v1-8k", alias="KIMI_MODEL")
    kimi_temperature: float = Field(default=0.7, alias="KIMI_TEMPERATURE")
    kimi_max_tokens: int = Field(default=4000, alias="KIMI_MAX_TOKENS")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    def get_provider_config(self, provider: str) -> Dict[str, Any]:
        """Get configuration for a specific LLM provider."""
        configs = {
            "openai": {
                "api_key": self.openai_api_key,
                "api_base": self.openai_api_base,
                "model": self.openai_model,
                "temperature": self.openai_temperature,
                "max_tokens": self.openai_max_tokens,
            },
            "qwen": {
                "api_key": self.qwen_api_key,
                "api_base": self.qwen_api_base,
                "model": self.qwen_model,
                "temperature": self.qwen_temperature,
                "max_tokens": self.qwen_max_tokens,
            },
            "zhipu": {
                "api_key": self.zhipu_api_key,
                "api_base": self.zhipu_api_base,
                "model": self.zhipu_model,
                "temperature": self.zhipu_temperature,
                "max_tokens": self.zhipu_max_tokens,
            },
            "kimi": {
                "api_key": self.kimi_api_key,
                "api_base": self.kimi_api_base,
                "model": self.kimi_model,
                "temperature": self.kimi_temperature,
                "max_tokens": self.kimi_max_tokens,
            },
        }
        return configs.get(provider, configs["openai"])


class CrawlerSettings(BaseSettings):
    """Web crawler configuration settings."""

    user_agent: str = Field(
        default="AutoScholar/0.1.0 (Research Tool)", alias="CRAWLER_USER_AGENT"
    )
    timeout: int = Field(default=30, alias="CRAWLER_TIMEOUT")
    max_retries: int = Field(default=3, alias="CRAWLER_MAX_RETRIES")
    retry_delay: int = Field(default=5, alias="CRAWLER_RETRY_DELAY")
    concurrent_limit: int = Field(default=3, alias="CRAWLER_CONCURRENT_LIMIT")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class SchedulerSettings(BaseSettings):
    """Task scheduler configuration settings."""

    crawl_cron: str = Field(default="0 8 * * *", alias="SCHEDULER_CRAWL_CRON")
    generate_cron: str = Field(default="0 9 * * *", alias="SCHEDULER_GENERATE_CRON")
    cleanup_cron: str = Field(default="0 2 * * 0", alias="SCHEDULER_CLEANUP_CRON")
    timezone: str = Field(default="Asia/Shanghai", alias="SCHEDULER_TIMEZONE")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )


class StorageSettings(BaseSettings):
    """Storage configuration settings."""

    reports_path: Path = Field(default=Path("./data/reports"), alias="STORAGE_REPORTS_PATH")
    temp_path: Path = Field(default=Path("./data/temp"), alias="STORAGE_TEMP_PATH")
    log_path: Path = Field(default=Path("./data/logs"), alias="STORAGE_LOG_PATH")
    log_retention_days: int = Field(default=90, alias="STORAGE_LOG_RETENTION_DAYS")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("reports_path", "temp_path", "log_path", mode="before")
    @classmethod
    def convert_to_path(cls, v: Any) -> Path:
        """Convert string to Path object."""
        if isinstance(v, str):
            return Path(v)
        return v

    def ensure_directories(self) -> None:
        """Ensure all storage directories exist."""
        for path in [self.reports_path, self.temp_path, self.log_path]:
            path.mkdir(parents=True, exist_ok=True)


class APISettings(BaseSettings):
    """API server configuration settings."""

    host: str = Field(default="0.0.0.0", alias="API_HOST")
    port: int = Field(default=8000, alias="API_PORT")
    api_key: str = Field(default="", alias="API_KEY")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000"], alias="API_CORS_ORIGINS"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v


class Settings:
    """Main settings class that aggregates all configuration."""

    def __init__(self) -> None:
        """Initialize all settings."""
        self.app = AppSettings()
        self.database = DatabaseSettings()
        self.llm = LLMSettings()
        self.crawler = CrawlerSettings()
        self.scheduler = SchedulerSettings()
        self.storage = StorageSettings()
        self.api = APISettings()

        # Ensure storage directories exist
        self.storage.ensure_directories()

    def __repr__(self) -> str:
        """String representation."""
        return f"Settings(env={self.app.env}, debug={self.app.debug})"


# Global settings instance
settings = Settings()
