"""End-to-end extraction flow tests (Phase 1, Stage 1.4.4).

Flow under test: stored config → extract text via (mocked) LLM →
pattern auto-saved → re-extract same layout → Search Library consulted
first (decision nº 2). With a hand-crafted regex pattern, the library
path extracts with zero LLM cost.
"""

from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from spec.core.config_store import ConfigStore
from spec.extraction.engine import ExtractionEngine
from spec.extraction.llm.factory import LLMProviderFactory
from spec.models.config import ExtractionConfig
from spec.models.extraction import ExtractionRequest
from spec.output.manager import OutputManager
from spec.search_library.json_storage import JSONStorage

_DOCUMENT = """Laudo de exame
Paciente: Maria Silva
Exame: Glicose
Resultado: 118 mg/dL
"""


def _config(config_id: str = "exames_v1") -> ExtractionConfig:
    return ExtractionConfig.model_validate(
        {
            "extraction_id": config_id,
            "name": "Exames",
            "input": {"type": "text"},
            "output": {"type": "json", "schema": {"exame": "string", "resultado": "string"}},
            "llm": {"provider": "google", "model": "gemini-2.5-flash"},
            "behavior": {
                "use_search_library": True,
                "auto_create_patterns": True,
                "layout_independent": True,
                "update_on_change": True,
            },
            "extraction_instructions": "Extraia exame e resultado.",
        }
    )


def _engine(tmp_path, llm_result: Dict[str, Any]) -> tuple[ExtractionEngine, AsyncMock]:
    store = ConfigStore(config_dir=str(tmp_path / "configs"))
    store.save(_config())

    fake_provider = AsyncMock()
    fake_provider.extract = AsyncMock(return_value=llm_result)
    factory = LLMProviderFactory()
    factory.get_provider = lambda **kwargs: fake_provider  # type: ignore[method-assign]

    engine = ExtractionEngine(
        search_library=JSONStorage(storage_path=str(tmp_path / "patterns.json")),
        llm_factory=factory,
        output_manager=OutputManager(),
        config_store=store,
    )
    return engine, fake_provider


class TestEndToEndFlow:
    @pytest.mark.asyncio
    async def test_llm_extraction_uses_config_and_saves_pattern(self, tmp_path):
        engine, provider = _engine(
            tmp_path, {"exame": "Glicose", "resultado": "118 mg/dL"}
        )

        response = await engine.extract(
            ExtractionRequest(
                config_id="exames_v1",
                source={"type": "text", "content": _DOCUMENT},
            )
        )

        assert response.status == "success"
        assert response.method_used == "llm"
        assert response.data == {"exame": "Glicose", "resultado": "118 mg/dL"}
        assert response.layout_fingerprint

        # Config-driven prompt: instructions and schema came from the store.
        kwargs = provider.extract.call_args.kwargs
        assert kwargs["instructions"] == "Extraia exame e resultado."
        assert kwargs["schema"] == {"fields": {"exame": "string", "resultado": "string"}}

        # Pattern was auto-saved, indexed by the fingerprint.
        patterns = await engine.search_library.list_patterns(config_id="exames_v1")
        assert len(patterns) == 1
        assert patterns[0]["fingerprint"] == response.layout_fingerprint

    @pytest.mark.asyncio
    async def test_library_hit_extracts_without_llm(self, tmp_path):
        engine, provider = _engine(tmp_path, {"never": "called"})

        # Seed the library with a working regex pattern for this layout.
        fingerprint = engine.fingerprint_generator.generate(_DOCUMENT)
        await engine.search_library.save_pattern(
            fingerprint,
            "exames_v1",
            {
                "fields": [
                    {
                        "field_name": "exame",
                        "extraction_method": "regex",
                        "pattern": r"Exame:\s*([^\n]+)",
                    },
                    {
                        "field_name": "resultado",
                        "extraction_method": "regex",
                        "pattern": r"Resultado:\s*([^\n]+)",
                    },
                ]
            },
        )

        response = await engine.extract(
            ExtractionRequest(
                config_id="exames_v1",
                source={"type": "text", "content": _DOCUMENT},
            )
        )

        assert response.status == "success"
        assert response.method_used == "search_library"
        assert response.data["exame"] == "Glicose"
        assert response.data["resultado"] == "118 mg/dL"
        provider.extract.assert_not_called()

    @pytest.mark.asyncio
    async def test_force_llm_bypasses_library(self, tmp_path):
        engine, provider = _engine(tmp_path, {"exame": "Glicose"})
        fingerprint = engine.fingerprint_generator.generate(_DOCUMENT)
        await engine.search_library.save_pattern(
            fingerprint,
            "exames_v1",
            {
                "fields": [
                    {
                        "field_name": "exame",
                        "extraction_method": "regex",
                        "pattern": r"Exame:\s*([^\n]+)",
                    }
                ]
            },
        )

        response = await engine.extract(
            ExtractionRequest(
                config_id="exames_v1",
                source={"type": "text", "content": _DOCUMENT},
                force_llm=True,
            )
        )

        assert response.method_used == "llm"
        provider.extract.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_config_falls_back_to_defaults(self, tmp_path):
        engine, provider = _engine(tmp_path, {"campo": "valor"})

        response = await engine.extract(
            ExtractionRequest(
                config_id="config_inexistente",
                source={"type": "text", "content": _DOCUMENT},
                options={"auto_create_patterns": False},
            )
        )

        assert response.status == "success"
        assert response.method_used == "llm"
        # No pattern saved when auto_create_patterns is off.
        patterns = await engine.search_library.list_patterns()
        assert patterns == []
