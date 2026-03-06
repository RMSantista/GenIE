"""OpenAI LLM provider implementation.

Note: This is a placeholder for Phase 2 implementation.
"""

from typing import Any, Dict

from spec.extraction.llm.base import BaseLLMProvider


class OpenAIProvider(BaseLLMProvider):
    """LLM provider for OpenAI's GPT models.

    Note:
        This is a placeholder implementation for Phase 2.
        Full functionality will be implemented in a future phase.
    """

    async def extract(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> Dict[str, Any]:
        """Extract data using OpenAI.

        Note:
            Not implemented in Phase 1. To be implemented in Phase 2.
        """

        raise NotImplementedError("OpenAI provider will be implemented in Phase 2")

    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> str:
        """Build prompt for OpenAI.

        Note:
            Not implemented in Phase 1.
        """

        raise NotImplementedError("OpenAI provider will be implemented in Phase 2")

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse OpenAI response.

        Note:
            Not implemented in Phase 1.
        """

        raise NotImplementedError("OpenAI provider will be implemented in Phase 2")
