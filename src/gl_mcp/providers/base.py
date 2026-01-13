"""Base provider class for MCP tool providers."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable

from gl_mcp.mcp.server import get_server_manager

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Base class for MCP tool providers.

    Each provider exposes a set of tools for a specific domain (e.g., news, jira).
    Providers handle credential loading and tool registration.
    """

    # Override in subclasses
    name: str = "base"
    required_role: str | None = None  # e.g., "gl-premium", "gl-admin"

    def __init__(self):
        self._credentials_loaded = False
        self._credentials_valid = False

    @abstractmethod
    async def load_credentials(self) -> bool:
        """Load and validate credentials for this provider.

        Returns:
            True if credentials are valid, False otherwise
        """
        pass

    @abstractmethod
    def register_tools(self) -> None:
        """Register tools with the MCP server manager."""
        pass

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
        handler: Callable,
    ) -> None:
        """Helper method to register a tool.

        Args:
            name: Tool name (will be prefixed with provider name)
            description: Human-readable description
            input_schema: JSON Schema for parameters
            handler: Async handler function
        """
        full_name = f"{self.name}_{name}"
        get_server_manager().register_tool(
            name=full_name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )

    async def initialize(self) -> bool:
        """Initialize the provider (load credentials and register tools).

        Returns:
            True if initialization successful
        """
        if self._credentials_loaded:
            return self._credentials_valid

        self._credentials_loaded = True
        self._credentials_valid = await self.load_credentials()

        if self._credentials_valid:
            self.register_tools()
            logger.info(f"Provider '{self.name}' initialized successfully")
        else:
            logger.warning(f"Provider '{self.name}' credentials invalid")

        return self._credentials_valid

    @property
    def is_available(self) -> bool:
        """Check if provider is available (credentials valid)."""
        return self._credentials_valid


class ProviderRegistry:
    """Registry for managing MCP providers."""

    def __init__(self):
        self._providers: dict[str, BaseProvider] = {}

    def register(self, provider: BaseProvider) -> None:
        """Register a provider."""
        self._providers[provider.name] = provider
        logger.debug(f"Registered provider: {provider.name}")

    async def initialize_all(self, user_roles: list[str] | None = None) -> dict[str, bool]:
        """Initialize all registered providers.

        Args:
            user_roles: Optional list of user roles for filtering

        Returns:
            Dict of provider name -> initialization status
        """
        results = {}
        for name, provider in self._providers.items():
            # Check role requirements
            if provider.required_role and user_roles is not None:
                if provider.required_role not in user_roles:
                    logger.debug(
                        f"Skipping provider '{name}' - requires role '{provider.required_role}'"
                    )
                    results[name] = False
                    continue

            results[name] = await provider.initialize()

        return results

    def get_provider(self, name: str) -> BaseProvider | None:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_available_providers(self, user_roles: list[str] | None = None) -> list[str]:
        """Get list of available provider names.

        Args:
            user_roles: Optional list of user roles for filtering

        Returns:
            List of available provider names
        """
        available = []
        for name, provider in self._providers.items():
            if provider.required_role and user_roles is not None:
                if provider.required_role not in user_roles:
                    continue
            if provider.is_available:
                available.append(name)
        return available

    async def check_all_credentials(self) -> dict[str, bool]:
        """Check credentials for all providers.

        Returns:
            Dict of provider name -> credential status
        """
        return {name: provider.is_available for name, provider in self._providers.items()}


# Global provider registry
_registry: ProviderRegistry | None = None


def get_provider_registry() -> ProviderRegistry:
    """Get or create the global provider registry."""
    global _registry
    if _registry is None:
        _registry = ProviderRegistry()
    return _registry


async def initialize_providers(user_roles: list[str] | None = None) -> dict[str, bool]:
    """Initialize all registered providers.

    Args:
        user_roles: Optional list of user roles for filtering

    Returns:
        Dict of provider name -> initialization status
    """
    return await get_provider_registry().initialize_all(user_roles)
