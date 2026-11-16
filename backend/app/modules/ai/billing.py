"""Pure cost arithmetic for the global AI budget. Amounts are integer micro-USD."""

import json
import math
from decimal import Decimal

from app.core.config import Settings

MICRO = Decimal(1_000_000)


def input_token_bound(messages: list[dict], schema: dict | None = None) -> int:
    """Upper bound of prompt tokens: every text token is at least one UTF-8 byte.

    The per-message allowance covers chat-template role/separator tokens. Every
    message sent to the model counts, including saved conversation history.
    """
    tokens = sum(len(m["content"].encode()) for m in messages) + 32 * len(messages)
    if schema is not None:
        # A response_format schema is billed as prompt tokens too.
        tokens += len(json.dumps(schema).encode())
    return tokens


def tariff_microusd(settings: Settings, input_tokens: int, output_tokens: int) -> int:
    """Cost at the configured per-million-token tariff, rounded up."""
    prompt, completion = settings.ai_input_price_per_mtok_usd, settings.ai_output_price_per_mtok_usd
    if prompt is None or completion is None:
        # Callers check pricing first; an unknown price is never zero.
        raise ValueError("AI tariff is not configured")
    # USD per million tokens is numerically micro-USD per token.
    return math.ceil(prompt * input_tokens + completion * output_tokens)


def budget_microusd(settings: Settings) -> int:
    return math.floor(settings.ai_daily_budget_usd * MICRO)


def settled_charge(settings: Settings, usage: dict | None) -> tuple[int, str] | None:
    """Charge from provider usage data, or None when it is not trustworthy.

    OpenRouter reports `usage.cost` in credits (1 credit = 1 USD). Without it,
    provider token counts priced at the configured tariff are a conservative bound
    (the tariff is also sent as max_price, so no endpoint charges more per token).
    """
    if not usage:
        return None
    cost = usage.get("cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and cost >= 0:
        return math.ceil(Decimal(str(cost)) * MICRO), "provider"
    prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
    if (
        isinstance(prompt, int)
        and isinstance(completion, int)
        and not isinstance(prompt, bool)
        and not isinstance(completion, bool)
        and prompt >= 0
        and completion >= 0
    ):
        return tariff_microusd(settings, prompt, completion), "tariff"
    return None
