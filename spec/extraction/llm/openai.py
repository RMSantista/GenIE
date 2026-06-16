"""OpenAI GPT LLM provider implementation."""

import json
import logging
from typing import Any, Dict

from openai import AsyncOpenAI

from spec.core.exceptions import LLMProviderError
from spec.extraction.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

_SYSTEM_MESSAGE = (
    "You are a specialized information extraction system. "
    "Return ONLY valid JSON, no explanations, no markdown, just raw JSON."
)


class OpenAIProvider(BaseLLMProvider):
    """LLM provider for OpenAI's GPT models.

    Uses the AsyncOpenAI client for non-blocking API calls.

    Attributes:
        client: AsyncOpenAI client instance
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        max_tokens: int = 8192,
        temperature: float = 0.0,
    ) -> None:
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: GPT model version
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Raises:
            LLMProviderError: If API key is missing
        """

        if not api_key:
            raise LLMProviderError("OpenAI API key is required")

        super().__init__(api_key, model)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = AsyncOpenAI(api_key=api_key)

    async def extract(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> Dict[str, Any]:
        """Extract data using GPT.

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

            logger.debug(f"Calling OpenAI API with model: {self.model}")

            response = await self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": _SYSTEM_MESSAGE},
                    {"role": "user", "content": prompt},
                ],
            )

            logger.debug("OpenAI API response received successfully")

            return self._parse_response(response)

        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Invalid JSON in OpenAI response: {e}")
        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"OpenAI API error: {e}", exc_info=True)
            raise LLMProviderError(f"OpenAI extraction failed: {e}")

    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> str:
        """Build optimized prompt for GPT.

        Args:
            content: Text content
            schema: Output schema
            instructions: User instructions

        Returns:
            str: Formatted prompt
        """

        schema_str = json.dumps(schema, indent=2, ensure_ascii=False)

        return f"""Extract information from the following document and return it as JSON.

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

    def _parse_response(self, response: Any) -> Dict[str, Any]:
        """Parse OpenAI response.

        Handles markdown code blocks and extracts JSON.

        Args:
            response: OpenAI API response object

        Returns:
            dict: Parsed JSON data

        Raises:
            LLMProviderError: If JSON parsing fails
        """

        text = response.choices[0].message.content.strip()

        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]

        if text.endswith("```"):
            text = text[:-3]

        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from OpenAI: {text[:100]}...")
            raise LLMProviderError(f"Invalid JSON response from OpenAI: {e}")
