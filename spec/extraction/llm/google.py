"""Google Gemini LLM provider implementation."""

import json
import logging
from typing import Any, Dict

from google import genai
from google.genai import types

from spec.core.exceptions import LLMProviderError
from spec.extraction.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTION = (
    "You are a specialized information extraction system. "
    "Return ONLY valid JSON, no explanations, no markdown, just raw JSON."
)


class GoogleProvider(BaseLLMProvider):
    """LLM provider for Google's Gemini models.

    Uses the google-genai SDK with native async support via client.aio.

    Attributes:
        client: genai.Client instance
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        max_tokens: int = 4096,
        temperature: float = 0.0,
    ) -> None:
        """Initialize Google Gemini provider.

        Args:
            api_key: Google AI API key
            model: Gemini model version
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature (0.0-1.0)

        Raises:
            LLMProviderError: If API key is missing
        """

        if not api_key:
            raise LLMProviderError("Google API key is required")

        super().__init__(api_key, model)
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.client = genai.Client(api_key=api_key)
        self._generate_config = types.GenerateContentConfig(
            system_instruction=_SYSTEM_INSTRUCTION,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

    async def extract(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> Dict[str, Any]:
        """Extract data using Gemini.

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

            logger.debug(f"Calling Gemini API with model: {self.model}")

            response = await self.client.aio.models.generate_content(
                model=self.model,
                contents=prompt,
                config=self._generate_config,
            )

            logger.debug("Gemini API response received successfully")

            return self._parse_response(response)

        except json.JSONDecodeError as e:
            raise LLMProviderError(f"Invalid JSON in Gemini response: {e}")
        except LLMProviderError:
            raise
        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise LLMProviderError(f"Gemini extraction failed: {e}")

    def _build_prompt(
        self,
        content: str,
        schema: Dict[str, Any],
        instructions: str = "",
    ) -> str:
        """Build optimized prompt for Gemini.

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
        """Parse Gemini response.

        Handles markdown code blocks and extracts JSON.

        Args:
            response: Gemini API response object

        Returns:
            dict: Parsed JSON data

        Raises:
            LLMProviderError: If JSON parsing fails
        """

        text = response.text.strip()

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
            logger.error(f"Failed to parse JSON from Gemini: {text[:100]}...")
            raise LLMProviderError(f"Invalid JSON response from Gemini: {e}")
