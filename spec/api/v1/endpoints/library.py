"""Search Library inspection endpoints (Phase 1, Stage 1.4.3)."""

import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException

from spec.api.v1.dependencies import get_search_library
from spec.search_library.json_storage import JSONStorage

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/patterns")
async def list_patterns(
    config_id: Optional[str] = None,
    library: JSONStorage = Depends(get_search_library),
) -> list[dict[str, Any]]:
    """List stored extraction patterns.

    Args:
        config_id: Optional filter by configuration id
        library: Search library storage (injected)

    Returns:
        list[dict]: Stored patterns
    """

    return await library.list_patterns(config_id=config_id)


@router.get("/patterns/{layout_id}")
async def get_pattern(
    layout_id: str,
    library: JSONStorage = Depends(get_search_library),
) -> dict[str, Any]:
    """Get a single pattern by layout id.

    Args:
        layout_id: Pattern layout identifier
        library: Search library storage (injected)

    Returns:
        dict: Pattern details

    Raises:
        HTTPException: 404 when the pattern does not exist
    """

    patterns = await library.list_patterns()
    pattern = next((p for p in patterns if p.get("layout_id") == layout_id), None)
    if pattern is None:
        raise HTTPException(
            status_code=404, detail=f"Padrão '{layout_id}' não encontrado"
        )
    return pattern


@router.get("/stats")
async def library_stats(
    library: JSONStorage = Depends(get_search_library),
) -> dict[str, Any]:
    """Aggregate statistics about the Search Library.

    Args:
        library: Search library storage (injected)

    Returns:
        dict: Metadata plus usage aggregates
    """

    metadata = await library.get_metadata()
    patterns = await library.list_patterns()

    total_uses = sum(p.get("use_count", 0) for p in patterns)
    avg_success = (
        round(sum(p.get("success_rate", 0.0) for p in patterns) / len(patterns), 3)
        if patterns
        else 0.0
    )
    by_config: dict[str, int] = {}
    for pattern in patterns:
        key = pattern.get("config_id", "?")
        by_config[key] = by_config.get(key, 0) + 1

    return {
        "metadata": metadata,
        "total_patterns": len(patterns),
        "total_uses": total_uses,
        "average_success_rate": avg_success,
        "patterns_by_config": by_config,
    }
