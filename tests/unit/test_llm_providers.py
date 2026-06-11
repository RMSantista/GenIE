"""Tests for LLM providers with mocked API clients (Phase 1, Stage 1.2.2)."""

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from spec.core.exceptions import InvalidConfig, LLMProviderError
from spec.extraction.llm.anthropic import AnthropicProvider
from spec.extraction.llm.factory import LLMProviderFactory
from spec.extraction.llm.google import GoogleProvider
from spec.extraction.llm.openai import OpenAIProvider

_SCHEMA = {"fields": {"exame": "string", "resultado": "string"}}
_PAYLOAD = {"exame": "Glicose", "resultado": "118 mg/dL"}


class TestPromptBuilding:
    def test_prompt_contains_content_schema_and_instructions(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant-test")
        prompt = provider._build_prompt("DOCUMENTO XYZ", _SCHEMA, "extraia exames")

        assert "DOCUMENTO XYZ" in prompt
        assert '"exame"' in prompt
        assert "extraia exames" in prompt

    def test_prompt_has_default_instructions(self) -> None:
        provider = OpenAIProvider(api_key="sk-test")
        prompt = provider._build_prompt("doc", _SCHEMA)

        assert "Extract all fields" in prompt


class TestResponseParsing:
    def test_anthropic_parses_markdown_wrapped_json(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant-test")
        response = SimpleNamespace(
            content=[SimpleNamespace(text=f"```json\n{json.dumps(_PAYLOAD)}\n```")]
        )

        assert provider._parse_response(response) == _PAYLOAD

    def test_openai_parses_plain_json(self) -> None:
        provider = OpenAIProvider(api_key="sk-test")
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(_PAYLOAD)))]
        )

        assert provider._parse_response(response) == _PAYLOAD

    def test_google_parses_code_fenced_json(self) -> None:
        provider = GoogleProvider(api_key="AIza-test")
        response = SimpleNamespace(text=f"```\n{json.dumps(_PAYLOAD)}\n```")

        assert provider._parse_response(response) == _PAYLOAD

    def test_invalid_json_raises_provider_error(self) -> None:
        provider = GoogleProvider(api_key="AIza-test")
        response = SimpleNamespace(text="isto não é JSON")

        with pytest.raises(LLMProviderError):
            provider._parse_response(response)


class TestExtractWithMockedClients:
    @pytest.mark.asyncio
    async def test_anthropic_extract(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant-test")
        provider.client = SimpleNamespace(
            messages=SimpleNamespace(
                create=AsyncMock(
                    return_value=SimpleNamespace(
                        content=[SimpleNamespace(text=json.dumps(_PAYLOAD))]
                    )
                )
            )
        )

        result = await provider.extract("doc", _SCHEMA, "extraia")

        assert result == _PAYLOAD
        kwargs = provider.client.messages.create.call_args.kwargs
        assert kwargs["model"] == provider.model
        assert "doc" in kwargs["messages"][0]["content"]

    @pytest.mark.asyncio
    async def test_openai_extract_uses_json_mode(self) -> None:
        provider = OpenAIProvider(api_key="sk-test")
        provider.client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(
                    create=AsyncMock(
                        return_value=SimpleNamespace(
                            choices=[
                                SimpleNamespace(
                                    message=SimpleNamespace(content=json.dumps(_PAYLOAD))
                                )
                            ]
                        )
                    )
                )
            )
        )

        result = await provider.extract("doc", _SCHEMA)

        assert result == _PAYLOAD
        kwargs = provider.client.chat.completions.create.call_args.kwargs
        assert kwargs["response_format"] == {"type": "json_object"}

    @pytest.mark.asyncio
    async def test_google_extract(self) -> None:
        provider = GoogleProvider(api_key="AIza-test")
        provider.client = SimpleNamespace(
            aio=SimpleNamespace(
                models=SimpleNamespace(
                    generate_content=AsyncMock(
                        return_value=SimpleNamespace(text=json.dumps(_PAYLOAD))
                    )
                )
            )
        )

        result = await provider.extract("doc", _SCHEMA)

        assert result == _PAYLOAD

    @pytest.mark.asyncio
    async def test_api_error_wrapped_as_provider_error(self) -> None:
        provider = AnthropicProvider(api_key="sk-ant-test")
        provider.client = SimpleNamespace(
            messages=SimpleNamespace(create=AsyncMock(side_effect=RuntimeError("boom")))
        )

        with pytest.raises(LLMProviderError, match="boom"):
            await provider.extract("doc", _SCHEMA)

    def test_missing_key_rejected(self) -> None:
        with pytest.raises(LLMProviderError):
            AnthropicProvider(api_key="")
        with pytest.raises(LLMProviderError):
            OpenAIProvider(api_key="")
        with pytest.raises(LLMProviderError):
            GoogleProvider(api_key="")


class TestFactory:
    def test_unknown_provider_rejected(self) -> None:
        with pytest.raises(InvalidConfig):
            LLMProviderFactory().get_provider("skynet", api_key="x")

    def test_provider_instances_are_cached(self) -> None:
        factory = LLMProviderFactory()
        a = factory.get_provider("openai", api_key="sk-test")
        b = factory.get_provider("openai", api_key="sk-test")

        assert a is b

    def test_cache_key_never_contains_key_material(self) -> None:
        factory = LLMProviderFactory()
        factory.get_provider("openai", api_key="sk-supersecret123")

        assert all("supersecret" not in k for k in factory._providers)

    def test_defaults_per_provider(self) -> None:
        factory = LLMProviderFactory()
        provider = factory.get_provider("google", api_key="AIza-test")

        assert provider.model == "gemini-2.5-flash"
