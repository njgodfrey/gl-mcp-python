"""MCP Providers - Each provider exposes tools for a specific domain."""

from gl_mcp.providers.base import (
    BaseProvider,
    ProviderRegistry,
    get_provider_registry,
    initialize_providers,
)
from gl_mcp.providers.jira import JiraProvider

__all__ = [
    "BaseProvider",
    "ProviderRegistry",
    "get_provider_registry",
    "initialize_providers",
    "JiraProvider",
]


def register_all_providers() -> None:
    """Register all available providers with the registry."""
    registry = get_provider_registry()

    # Register providers
    registry.register(JiraProvider())

    # Add more providers here as they are implemented:
    # registry.register(NewsProvider())
    # registry.register(VaultProvider())
    # registry.register(AdminProvider())
