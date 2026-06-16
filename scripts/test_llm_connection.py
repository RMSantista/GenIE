#!/usr/bin/env python3
"""Manual LLM connectivity test (Phase 1, Stage 1.2.2).

Usage:
    python3 scripts/test_llm_connection.py [provider]

Resolves the API key from the encrypted vault first, then from env vars
(GOOGLE_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY).
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spec.extraction.llm.factory import LLMProviderFactory  # noqa: E402


async def main() -> int:
    """Run a minimal extraction against the chosen provider.

    Returns:
        int: Process exit code (0 = success)
    """

    provider_name = sys.argv[1] if len(sys.argv) > 1 else "google"
    factory = LLMProviderFactory()

    print(f"Testing provider: {provider_name}")
    try:
        provider = factory.get_provider(provider_name=provider_name)
        result = await provider.extract(
            content="ping",
            schema={"ok": True},
            instructions='Responda apenas com o JSON {"ok": true}.',
        )
    except Exception as e:  # noqa: BLE001 - CLI feedback
        print(f"✗ FALHOU: {e}")
        return 1

    print(f"✓ OK — resposta: {result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
