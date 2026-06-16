"""Organizer agent: reshapes extracted records into the requested output format."""

import json
import logging
from typing import Any, Callable, Dict, List, Tuple

from spec.core.exceptions import LLMProviderError
from spec.extraction.llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

EmitFn = Callable[..., None]

_MAX_RECORDS_PER_CALL = 60

_SCHEMA: Dict[str, Any] = {
    "formatted": ["...payloads no formato pedido, prontos para entrega..."],
    "delivery_hints": {"method": "POST", "headers": {}, "batch": True},
}

_INSTRUCTIONS_TEMPLATE = """Você é o Organizador do GenIE. Reformate os dados extraídos no formato pedido pelo usuário.

Formato de saída desejado:
{output_format}

Tipo de destino: {output_type}

Regras:
- "formatted" é uma lista de payloads prontos para o Conector entregar, um por registro (a menos que o formato peça agrupamento).
- Normalize datas para ISO-8601 e números para tipos numéricos quando possível.
- Não descarte registros: em caso de dúvida, inclua o registro com um campo "_warnings" (lista de strings).
- "delivery_hints" indica como entregar (method, headers extras, batch true/false).
- Responda APENAS com JSON válido no formato do schema.
"""


class OrganizerAgent:
    """Formatting layer of the GenIE pipeline."""

    def __init__(self, provider: BaseLLMProvider) -> None:
        """Initialize the agent.

        Args:
            provider: LLM provider used for formatting
        """

        self.provider = provider

    async def run(
        self,
        records: List[Dict[str, Any]],
        output_format: str,
        output_type: str,
        emit: EmitFn,
    ) -> Tuple[List[Any], Dict[str, Any]]:
        """Format records per the user instruction.

        When no format instruction is given, records pass through unchanged
        (zero LLM cost), honoring GenIE's cost-efficiency principle.

        Args:
            records: Records extracted by the Locator
            output_format: Free-text formatting instruction (may be empty)
            output_type: Destination kind (url/path/db/api/download)
            emit: Event emitter (agent fixed to "organizador" by caller)

        Returns:
            tuple: (formatted payloads, delivery hints)
        """

        if not records:
            emit(message="Nenhum registro para formatar")
            return [], {}

        if not output_format.strip():
            emit(
                message=f"Sem instrução de formato — entregando {len(records)} registro(s) como JSON"
            )
            return list(records), {}

        instructions = _INSTRUCTIONS_TEMPLATE.format(
            output_format=output_format.strip(), output_type=output_type
        )

        formatted: List[Any] = []
        hints: Dict[str, Any] = {}

        batches = [
            records[i : i + _MAX_RECORDS_PER_CALL]
            for i in range(0, len(records), _MAX_RECORDS_PER_CALL)
        ]
        for batch_idx, batch in enumerate(batches, 1):
            emit(
                message=f"Formatando lote {batch_idx}/{len(batches)} ({len(batch)} registro(s))",
                progress=int(batch_idx / len(batches) * 90),
            )
            payload = json.dumps(batch, ensure_ascii=False, indent=1, default=str)
            try:
                parsed = await self.provider.extract(
                    content=f"Dados brutos (JSON):\n{payload}",
                    schema=_SCHEMA,
                    instructions=instructions,
                )
            except LLMProviderError as e:
                emit(
                    message=f"Organizador indisponível ({e}) — usando registros brutos",
                    level="error",
                )
                formatted.extend(batch)
                continue

            batch_formatted = (
                parsed.get("formatted") if isinstance(parsed, dict) else parsed
            )
            if isinstance(batch_formatted, dict):
                batch_formatted = [batch_formatted]
            if isinstance(batch_formatted, list) and batch_formatted:
                formatted.extend(batch_formatted)
            else:
                formatted.extend(batch)

            if isinstance(parsed, dict) and isinstance(
                parsed.get("delivery_hints"), dict
            ):
                hints = parsed["delivery_hints"]

        return formatted, hints
