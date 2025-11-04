"""Test configuration module."""

from app.core.config import Settings


def test_settings_initialization():
    """Test settings initialization."""
    settings = Settings()
    assert settings.app.name == "AutoScholar"
    assert settings.app.version is not None
    assert settings.database.port == 5432


def test_llm_provider_config():
    """Test LLM provider configuration."""
    settings = Settings()
    
    # Test default provider
    assert settings.llm.default_provider in ["openai", "qwen", "zhipu", "kimi"]
    
    # Test getting provider config
    config = settings.llm.get_provider_config("openai")
    assert "api_key" in config
    assert "model" in config
    assert "temperature" in config
