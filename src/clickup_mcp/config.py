"""Configuration management for ClickUp MCP server."""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from platformdirs import user_config_dir
from pydantic import BaseModel, Field, SecretStr, field_validator, ConfigDict


class ConfigError(Exception):
    """Configuration related errors."""

    pass


class IDPattern(BaseModel):
    """Custom ID pattern configuration."""

    prefix: str
    description: str


class ConfigModel(BaseModel):
    """Configuration model for the server."""

    api_key: SecretStr
    default_workspace_id: Optional[str] = None
    default_team_id: Optional[str] = None
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")
    id_patterns: Dict[str, str] = Field(
        default_factory=lambda: {"gh": "GitHub Issues", "GH": "GitHub Issues"},
        description="Custom ID patterns like {'gh': 'GitHub Issues'}",
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: SecretStr) -> SecretStr:
        """Validate API key format."""
        key = v.get_secret_value()
        if not key or len(key) < 10:
            raise ValueError("Invalid API key format")
        return v


class Config(BaseModel):
    """Main configuration class with multiple source support."""

    model_config = ConfigDict(
        extra="ignore",
    )

    api_key: str = Field(description="ClickUp API key")
    default_workspace_id: Optional[str] = None
    default_team_id: Optional[str] = None
    cache_ttl: int = 300
    id_patterns: Dict[str, str] = Field(
        default_factory=lambda: {"gh": "GitHub Issues", "GH": "GitHub Issues"}
    )

    def __init__(self, **kwargs: Any) -> None:
        """Initialize config from multiple sources."""
        # Try to load from config files first
        config_data = self._load_from_files()

        # Add environment variables with our prefix
        env_data = self._get_filtered_env_vars()
        config_data.update(env_data)

        # Merge with any provided kwargs (highest priority)
        config_data.update(kwargs)

        # Use BaseModel init to avoid BaseSettings environment processing
        super().__init__(**config_data)

        # Validate we have required fields
        if not self.api_key:
            raise ConfigError(
                "No API key found. Please configure CLICKUP_MCP_API_KEY or create a config file."
            )

    def _load_from_files(self) -> Dict[str, Any]:
        """Load configuration from standard file locations."""
        config_locations = [
            # XDG standard location (preferred)
            Path.home() / ".config" / "clickup-mcp" / "config.json",
            # Platform-specific location (e.g., ~/Library/Application Support on macOS)
            Path(user_config_dir("clickup-mcp")) / "config.json",
            # Fallback home directory location
            Path.home() / ".clickup-mcp" / "config.json",
        ]

        # Also check XDG_CONFIG_HOME if set
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config:
            config_locations.insert(1, Path(xdg_config) / "clickup-mcp" / "config.json")

        for config_path in config_locations:
            if config_path.exists():
                try:
                    with open(config_path, "r") as f:
                        data = json.load(f)
                        # Validate with pydantic model
                        ConfigModel(**data)
                        return data
                except json.JSONDecodeError as e:
                    raise ConfigError(f"Invalid JSON in {config_path}: {e}") from e
                except Exception as e:
                    raise ConfigError(f"Error loading config from {config_path}: {e}") from e

        return {}

    def _get_filtered_env_vars(self) -> Dict[str, Any]:
        """Get environment variables with our prefix only."""
        env_data = {}
        prefix = "CLICKUP_MCP_"
        
        # Only process environment variables with our specific prefix
        for key, value in os.environ.items():
            if key.startswith(prefix) and value:
                # Remove prefix and convert to lowercase for field mapping
                field_name = key[len(prefix):].lower()
                env_data[field_name] = value
                
        return env_data

    def save_to_file(self, path: Optional[Path] = None) -> None:
        """Save current configuration to file."""
        if path is None:
            path = Path(user_config_dir("clickup-mcp")) / "config.json"

        path.parent.mkdir(parents=True, exist_ok=True)

        config_data = {
            "api_key": self.api_key,
        }

        if self.default_workspace_id:
            config_data["default_workspace_id"] = self.default_workspace_id

        if self.default_team_id:
            config_data["default_team_id"] = self.default_team_id

        if self.id_patterns:
            config_data["id_patterns"] = self.id_patterns

        if self.cache_ttl != 300:
            config_data["cache_ttl"] = self.cache_ttl

        with open(path, "w") as f:
            json.dump(config_data, f, indent=2)

    @property
    def headers(self) -> Dict[str, str]:
        """Get headers for ClickUp API requests."""
        return {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }
