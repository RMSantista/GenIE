"""Tests for PatternMatcher and JSONStorage behaviors (Phase 1, Stage 1.4.1)."""

import pytest

from spec.search_library.json_storage import JSONStorage
from spec.search_library.matcher import PatternMatcher

_CONTENT = """Paciente: Maria Silva
Exame: Glicose
Resultado: 118 mg/dL
"""

_PATTERN = {
    "fields": [
        {
            "field_name": "exame",
            "extraction_method": "regex",
            "pattern": r"Exame:\s*([^\n]+)",
            "validation": r".{2,}",
        },
        {
            "field_name": "resultado",
            "extraction_method": "regex",
            "pattern": r"Resultado:\s*([^\n]+)",
        },
    ]
}


class TestPatternMatcher:
    @pytest.mark.asyncio
    async def test_extracts_fields_with_regex(self) -> None:
        data = await PatternMatcher.extract_with_pattern(_CONTENT, _PATTERN)

        assert data == {"exame": "Glicose", "resultado": "118 mg/dL"}

    @pytest.mark.asyncio
    async def test_missing_match_yields_none(self) -> None:
        data = await PatternMatcher.extract_with_pattern("sem nada aqui", _PATTERN)

        assert data == {"exame": None, "resultado": None}

    @pytest.mark.asyncio
    async def test_empty_or_invalid_patterns_are_safe(self) -> None:
        pattern = {
            "fields": [
                {"field_name": "vazio", "extraction_method": "regex", "pattern": ""},
                {"field_name": "quebrado", "extraction_method": "regex", "pattern": "(["},
                {"field_name": "futuro", "extraction_method": "instruction"},
                {"field_name": "estranho", "extraction_method": "telepatia"},
            ]
        }

        data = await PatternMatcher.extract_with_pattern(_CONTENT, pattern)

        assert data == {
            "vazio": None,
            "quebrado": None,
            "futuro": None,
            "estranho": None,
        }

    @pytest.mark.asyncio
    async def test_validation_passes_and_fails(self) -> None:
        ok = await PatternMatcher.validate_extraction(
            {"exame": "Glicose", "resultado": "118 mg/dL"}, _PATTERN
        )
        assert ok is True

        bad = await PatternMatcher.validate_extraction({"exame": "X"}, _PATTERN)
        assert bad is False  # validation r".{2,}" rejects 1-char value

    @pytest.mark.asyncio
    async def test_validation_skips_none_values(self) -> None:
        ok = await PatternMatcher.validate_extraction(
            {"exame": None, "resultado": "118"}, _PATTERN
        )
        assert ok is True


class TestJsonStorage:
    @pytest.fixture
    def storage(self, tmp_path) -> JSONStorage:
        return JSONStorage(storage_path=str(tmp_path / "patterns.json"))

    @pytest.mark.asyncio
    async def test_find_increments_use_count(self, storage: JSONStorage) -> None:
        await storage.save_pattern("fp-1", "cfg", {"fields": []})

        first = await storage.find_pattern("fp-1", "cfg")
        assert first is not None
        count_after_first = first["use_count"]

        second = await storage.find_pattern("fp-1", "cfg")
        assert second["use_count"] == count_after_first + 1
        assert await storage.find_pattern("fp-2", "cfg") is None
        assert await storage.find_pattern("fp-1", "outra_cfg") is None

    @pytest.mark.asyncio
    async def test_success_rate_moving_average(self, storage: JSONStorage) -> None:
        await storage.save_pattern("fp-1", "cfg", {"fields": []})
        await storage.find_pattern("fp-1", "cfg")  # use_count -> 2

        await storage.update_success_rate("fp-1", success=False)

        patterns = await storage.list_patterns()
        assert patterns[0]["success_rate"] < 1.0

    @pytest.mark.asyncio
    async def test_metadata_tracks_totals(self, storage: JSONStorage) -> None:
        await storage.save_pattern("fp-1", "cfg-a", {"fields": []})
        await storage.save_pattern("fp-2", "cfg-b", {"fields": []})

        metadata = await storage.get_metadata()
        assert metadata["total_patterns"] == 2

        only_a = await storage.list_patterns(config_id="cfg-a")
        assert len(only_a) == 1

    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, storage: JSONStorage, tmp_path) -> None:
        await storage.save_pattern("fp-1", "cfg", {"fields": []})

        reopened = JSONStorage(storage_path=str(tmp_path / "patterns.json"))
        patterns = await reopened.list_patterns()
        assert len(patterns) == 1
