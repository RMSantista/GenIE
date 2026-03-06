"""Base class for LLM provider abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseLLMProvider(ABC):
    """Abstract base class for LLM providers.

    All LLM providers must inherit from this class and implement
    the abstract methods.

    Attributes:
        api_key: API key for the provider
        model: Model identifier
    """

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize LLM provider.

        Args:
            api_key: API key for authentication
            model: Model identifier (e.g., "claude-sonnet-4-20250514")
        """

        self.api_key = api_key
        self.model = model

    @abstractmethod
    async def extract(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> Dict[str, Any]:
        """Extract structured data from content.

        Args:
            content: Text content to analyze
            schema: Expected output schema
            instructions: Extraction instructions/context

        Returns:
            dict: Extracted data matching the schema

        Raises:
            LLMProviderError: If extraction fails
        """

        pass

    @abstractmethod
    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> str:
        """Build prompt for the LLM.

        Args:
            content: Text content
            schema: Output schema
            instructions: Extraction instructions

        Returns:
            str: Formatted prompt for the LLM
        """

        pass

    @abstractmethod
    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse LLM response into structured data.

        Args:
            response: Raw response from LLM

        Returns:
            dict: Parsed structured data

        Raises:
            LLMProviderError: If parsing fails
        """

        pass
