"""Locator agent: extracts the requested information from each item via LLM."""

import asyncio
import logging
from typing import Any, Callable, Dict, List, Tuple

from spec.core.exceptions import ExtractionFailed, LLMProviderError
from spec.extraction.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

EmitFn = Callable[..., None]

_MAX_CHUNK_CHARS = 24_000
_CHUNK_OVERLAP = 500
_MAX_RETRIES = 3
_RETRYABLE_MARKERS = ("429", "503", "rate", "overload", "timeout", "temporarily")

_SCHEMA: Dict[str, Any] = {
    "records": [{"...campos extraídos conforme a instrução...": "valor"}],
    "confidence": 0.0,
    "notes": "observações curtas, se houver",
}

_INSTRUCTIONS_TEMPLATE = """Você é o Localizador do GenIE. Sua tarefa é extrair informações específicas do documento fornecido.

Instrução do usuário:
{user_prompt}

Regras:
- Responda APENAS com JSON válido no formato do schema.
- "records" é uma lista de objetos; cada objeto usa nomes de campos claros e consistentes derivados da instrução do usuário.
- Se nada relevante for encontrado, devolva "records": [].
- "confidence" entre 0.0 e 1.0.
"""


def _chunk(text: str) -> List[str]:
    """Split long content into overlapping chunks that fit a single call.

    Args:
        text: Item content

    Returns:
        list[str]: One or more chunks
    """

    if len(text) <= _MAX_CHUNK_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + _MAX_CHUNK_CHARS])
        start += _MAX_CHUNK_CHARS - _CHUNK_OVERLAP
    return chunks


class LocatorAgent:
    """Extraction layer of the GenIE pipeline (the only stage that reads documents)."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        """Initialize the agent.

        Args:
            provider: LLM provider used for extraction
        """

        self.provider = provider

    async def run(
        self,
        items: List[Dict[str, Any]],
        prompt: str,
        emit: EmitFn,
    ) -> Tuple[List[Dict[str, Any]], float, List[str]]:
        """Extract records from every item.

        Args:
            items: Content items from the Connector
            prompt: User extraction instruction
            emit: Event emitter (agent fixed to "localizador" by caller)

        Returns:
            tuple: (records, mean confidence, notes)

        Raises:
            ExtractionFailed: If every item fails
        """

        instructions = _INSTRUCTIONS_TEMPLATE.format(user_prompt=prompt.strip())

        records: List[Dict[str, Any]] = []
        confidences: List[float] = []
        notes: List[str] = []
        failures = 0

        total_chunks = sum(len(_chunk(item["content"])) for item in items)
        done_chunks = 0

        for item in items:
            chunks = _chunk(item["content"])
            for chunk_idx, chunk in enumerate(chunks, 1):
                done_chunks += 1
                suffix = (
                    f" (parte {chunk_idx}/{len(chunks)})" if len(chunks) > 1 else ""
                )
                emit(
                    message=f"Analisando {item['name']}{suffix}",
                    progress=int(done_chunks / max(total_chunks, 1) * 90),
                )
                document = f"Documento (id={item['id']}, nome={item['name']}):\n---\n{chunk}\n---"
                try:
                    parsed = await self._extract_with_retry(
                        document, instructions, emit
                    )
                except LLMProviderError as e:
                    failures += 1
                    emit(message=f"Falha em {item['name']}: {e}", level="error")
                    continue

                item_records = (
                    parsed.get("records") if isinstance(parsed, dict) else parsed
                )
                if isinstance(item_records, dict):
                    item_records = [item_records]
                if isinstance(item_records, list):
                    found = [r for r in item_records if isinstance(r, dict)]
                    records.extend(found)
                    if found:
                        emit(
                            message=f"{len(found)} registro(s) em {item['name']}{suffix}"
                        )
                if isinstance(parsed, dict):
                    if isinstance(parsed.get("confidence"), (int, float)):
                        confidences.append(float(parsed["confidence"]))
                    if parsed.get("notes"):
                        notes.append(str(parsed["notes"]))

        if failures and not records:
            raise ExtractionFailed(
                f"Extração falhou em todos os {failures} documento(s)/lote(s). "
                "Verifique a chave de API e o modelo selecionado."
            )

        confidence = (
            round(sum(confidences) / len(confidences), 2) if confidences else 0.0
        )
        return records, confidence, notes

    async def _extract_with_retry(
        self, document: str, instructions: str, emit: EmitFn
    ) -> Dict[str, Any]:
        """Call the LLM with exponential backoff on transient errors.

        Args:
            document: Document chunk wrapped with id/name header
            instructions: Locator system instructions
            emit: Event emitter

        Returns:
            dict: Parsed JSON from the model

        Raises:
            LLMProviderError: After exhausting retries
        """

        delay = 2.0
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return await self.provider.extract(
                    content=document,
                    schema=_SCHEMA,
                    instructions=instructions,
                )
            except LLMProviderError as e:
                transient = any(m in str(e).lower() for m in _RETRYABLE_MARKERS)
                if attempt == _MAX_RETRIES or not transient:
                    raise
                emit(
                    message=f"Erro transitório do provedor (tentativa {attempt}/{_MAX_RETRIES}), aguardando {delay:.0f}s…",
                    level="error",
                )
                await asyncio.sleep(delay)
                delay *= 2
        raise LLMProviderError("Retries exhausted")  # pragma: no cover
