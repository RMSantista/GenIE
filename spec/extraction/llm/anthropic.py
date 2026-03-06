"""Anthropic (Claude) LLM provider implementation."""

import json
import logging
from typing import Any, Dict

from anthropic import AsyncAnthropic

from spec.core.exceptions import LLMProviderError
from spec.extraction.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseLLMProvider):
    """LLM provider for Anthropic's Claude model.

    Uses the AsyncAnthropic client for non-blocking API calls.

    Attributes:
        client: AsyncAnthropic client instance
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> None:
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Claude model version
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Raises:
            LLMProviderError: If API key is missing
        """

        if not api_key:
            raise LLMProviderError("Anthropic API key is required")

        super().__init__(api_key, model)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = AsyncAnthropic(api_key=api_key)

    async def extract(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> Dict[str, Any]:
        """Extract data using Claude.

        Args:
            content: Text to analyze
            schema: Expected output schema
            instructions: Extraction instructions

        Returns:
            dict: Extracted data

        Raises:
            LLMProviderError: If extraction fails
        """

        try:
            prompt = self._build_prompt(content, schema, instructions)

            logger.debug(f"Calling Claude API with model: {self.model}")

            response = await self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                system=(
                    "You are a specialized information extraction system. "
                    "Return ONLY valid JSON, no explanations, no markdown, just raw JSON."
                ),
            )

            logger.debug("Claude API response received successfully")

            return self._parse_response(response)

        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Invalid JSON in Claude response: {e}")
        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            raise LLMProviderError(f"Claude extraction failed: {e}")

    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> str:
        """Build optimized prompt for Claude.

        Args:
            content: Text content
            schema: Output schema
            instructions: User instructions

        Returns:
            str: Formatted prompt
        """

        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

        prompt = f"""Extract information from the following document and return it as JSON.

DOCUMENT:
{content}

EXPECTED OUTPUT SCHEMA:
{schema_str}

EXTRACTION INSTRUCTIONS:
{instructions if instructions else "Extract all fields from the document that match the schema. Use null for missing fields."}

RULES:
1. Return ONLY a valid JSON object
2. Use exact field names from the schema
3. Use null for missing or unknown values
4. Preserve data types specified in the schema
5. Do not include any text outside the JSON object

JSON OUTPUT:
"""

        return prompt

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse Claude response.

        Handles markdown code blocks and extracts JSON.

        Args:
            response: Claude API response object

        Returns:
            dict: Parsed JSON data

        Raises:
            LLMProviderError: If JSON parsing fails
        """

        text = response.content[0].text.strip()

        # Remove markdown code blocks if present
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        # Parse JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {text[:100]}...")
            raise LLMProviderError(f"Invalid JSON response from Claude: {e}")
