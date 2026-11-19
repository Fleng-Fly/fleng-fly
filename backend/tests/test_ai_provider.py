import json

import httpx
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.errors import ApiError
from app.modules.ai.provider import OpenRouterProvider


def settings(**kwargs):
    return Settings(
        **{
            "ai_enabled": True,
            "openrouter_api_key": "test-only-key",
            "openrouter_model": "test/model",
            "ai_input_price_per_mtok_usd": "0.15",
            "ai_output_price_per_mtok_usd": "0.60",
            **kwargs,
        }
    )


async def test_openrouter_request_and_usage():
    def handler(request):
        assert str(request.url) == "https://openrouter.ai/api/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-only-key"
        body = json.loads(request.content)
        assert body["max_tokens"] == 800
        assert "response_format" not in body
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
                "usage": {"total_tokens": 12, "secret": "discard"},
            },
        )

    result = await OpenRouterProvider(settings(), httpx.MockTransport(handler)).complete(
        [{"role": "user", "content": "Hi"}], {"type": "object"}
    )
    assert result.content == "Hello!"
    assert result.usage == {"total_tokens": 12}


@pytest.mark.parametrize(
    "config",
    [Settings(), Settings(ai_enabled=True), Settings(ai_enabled=True, openrouter_api_key="key")],
)
async def test_missing_configuration(config):
    with pytest.raises(ApiError) as exc:
        await OpenRouterProvider(config).complete([])
    assert exc.value.status_code == 503


def test_invalid_model_and_url():
    with pytest.raises(ValidationError):
        Settings(openrouter_model="invalid model")
    with pytest.raises(ValidationError):
        Settings(openrouter_base_url="http://untrusted.example")


@pytest.mark.parametrize("status,expected", [(401, 503), (402, 503), (429, 429), (500, 503)])
async def test_provider_errors_redacted(status, expected):
    provider = OpenRouterProvider(
        settings(), httpx.MockTransport(lambda r: httpx.Response(status, text="secret-key"))
    )
    with pytest.raises(ApiError) as exc:
        await provider.complete([])
    assert exc.value.status_code == expected
    assert "secret-key" not in str(exc.value)


async def test_timeout():
    def handler(request):
        raise httpx.ReadTimeout("secret", request=request)

    with pytest.raises(ApiError) as exc:
        await OpenRouterProvider(settings(), httpx.MockTransport(handler)).complete([])
    assert exc.value.code == "AI_TIMEOUT"


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"choices": []},
        {"choices": [{"finish_reason": "length", "message": {"content": "partial"}}]},
        {"choices": [{"finish_reason": "stop", "message": {"content": None}}]},
    ],
)
async def test_invalid_completions(data):
    with pytest.raises(ApiError):
        await OpenRouterProvider(
            settings(), httpx.MockTransport(lambda r: httpx.Response(200, json=data))
        ).complete([])


async def test_structured_output_opt_in():
    def handler(request):
        format = json.loads(request.content)["response_format"]
        assert format["type"] == "json_schema"
        assert format["json_schema"]["schema"]["additionalProperties"] is False
        assert "required" in format["json_schema"]["schema"]
        return httpx.Response(
            200, json={"choices": [{"finish_reason": "stop", "message": {"content": "{}"}}]}
        )

    await OpenRouterProvider(
        settings(ai_structured_outputs=True), httpx.MockTransport(handler)
    ).complete([], {"type": "object"})


@pytest.mark.parametrize(
    "ending,success",
    [
        ('data: {"choices":[{"delta":{},"finish_reason":"stop"}]}\n\ndata: [DONE]\n\n', True),
        ("", False),
        ('data: {"error":{"message":"secret"}}\n\ndata: [DONE]\n\n', False),
        ('data: {"choices":[{"delta":{},"finish_reason":"length"}]}\n\ndata: [DONE]\n\n', False),
    ],
)
async def test_stream_framing_and_incomplete(ending, success):
    data = ': OPENROUTER PROCESSING\n\ndata: {"choices":[{"delta":{"content":"Hi"}}]}\n\n' + ending
    provider = OpenRouterProvider(
        settings(), httpx.MockTransport(lambda r: httpx.Response(200, text=data))
    )
    chunks = []
    try:
        async for chunk in provider.stream([]):
            chunks.append(chunk.content)
        assert success
    except ApiError:
        assert not success
    assert chunks[0] == "Hi"


@pytest.mark.parametrize("data", [[], {"choices": [None]}, {"choices": [{"message": []}]}])
async def test_malformed_provider_shapes_are_sanitized(data):
    with pytest.raises(ApiError) as exc:
        await OpenRouterProvider(
            settings(), httpx.MockTransport(lambda r: httpx.Response(200, json=data))
        ).complete([])
    assert exc.value.code == "AI_INVALID_RESPONSE"


@pytest.mark.parametrize("status,code", [(429, "AI_RATE_LIMITED"), (503, "AI_UNAVAILABLE")])
async def test_stream_provider_http_errors(status, code):
    provider = OpenRouterProvider(
        settings(), httpx.MockTransport(lambda r: httpx.Response(status, text="private"))
    )
    with pytest.raises(ApiError) as exc:
        _ = [chunk async for chunk in provider.stream([])]
    assert exc.value.code == code
    assert "private" not in str(exc.value)


# ── OpenRouter Auto Router (`openrouter/auto`) ───────────────────────────────

AUTO = {"openrouter_model": "openrouter/auto", "ai_allow_auto_router": True}


@pytest.mark.parametrize(
    "overrides,reason",
    [
        ({"openrouter_model": "openrouter/auto"}, "auto_router_not_enabled"),
        ({**AUTO, "ai_input_price_per_mtok_usd": None}, "missing_pricing"),
        ({**AUTO, "ai_output_price_per_mtok_usd": None}, "missing_pricing"),
        ({**AUTO}, None),
        # The opt-in covers exactly one id; other routers and :online models stay refused.
        ({**AUTO, "openrouter_model": "openrouter/free"}, "unsupported_model"),
        ({**AUTO, "openrouter_model": "openrouter/auto-beta"}, "unsupported_model"),
        (
            {"ai_allow_auto_router": True, "openrouter_model": "openai/gpt-4o:online"},
            "unsupported_model",
        ),
        ({"ai_allow_auto_router": True, "openrouter_model": "openai/gpt-4o-mini"}, None),
        ({"openrouter_model": "openai/gpt-4o-mini"}, None),
    ],
)
def test_model_validation(overrides, reason):
    from app.modules.ai.provider import unavailable_reason

    assert unavailable_reason(settings(**overrides)) == reason


async def test_auto_request_carries_the_price_ceiling_and_records_the_routed_model():
    seen = {}

    def handler(request):
        seen.update(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "model": "anthropic/claude-3.5-haiku",
                "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.000123},
            },
        )

    result = await OpenRouterProvider(settings(**AUTO), httpx.MockTransport(handler)).complete(
        [{"role": "user", "content": "Hi"}]
    )
    assert seen["model"] == "openrouter/auto" and seen["max_tokens"] == 800
    assert seen["provider"]["max_price"] == {"prompt": 0.15, "completion": 0.6, "request": 0}
    assert result.model == "anthropic/claude-3.5-haiku"
    assert result.usage["cost"] == 0.000123


@pytest.mark.parametrize("routed", [None, "", "x" * 400, 5, "has space/and bad", "a/<b>"])
async def test_unknown_or_malformed_routed_model_falls_back_to_the_configured_id(routed):
    body = {
        "choices": [{"message": {"content": "Hello!"}, "finish_reason": "stop"}],
        "usage": {"cost": 0.0001},
    }
    if routed is not None:
        body["model"] = routed
    result = await OpenRouterProvider(
        settings(**AUTO), httpx.MockTransport(lambda r: httpx.Response(200, json=body))
    ).complete([{"role": "user", "content": "Hi"}])
    assert result.model == "openrouter/auto"


async def test_concrete_model_ignores_the_response_model_field():
    body = {
        "model": "evil/other",
        "choices": [{"message": {"content": "Hi"}, "finish_reason": "stop"}],
    }
    result = await OpenRouterProvider(
        settings(), httpx.MockTransport(lambda r: httpx.Response(200, json=body))
    ).complete([{"role": "user", "content": "Hi"}])
    assert result.model == "test/model"


@pytest.mark.parametrize(
    "status,code", [(429, "AI_RATE_LIMITED"), (402, "AI_UNAVAILABLE"), (500, "AI_UNAVAILABLE")]
)
async def test_auto_router_provider_errors_are_mapped_without_leaking(status, code):
    transport = httpx.MockTransport(lambda r: httpx.Response(status, text="secret-key-detail"))
    with pytest.raises(ApiError) as exc:
        await OpenRouterProvider(settings(**AUTO), transport).complete(
            [{"role": "user", "content": "Hi"}]
        )
    assert "secret" not in exc.value.message.lower()
    assert exc.value.status_code in (429, 503)


def test_billing_for_auto_trusts_only_provider_reported_cost():
    from app.modules.ai import billing

    auto, concrete = settings(**AUTO), settings()
    tokens = {"prompt_tokens": 1000, "completion_tokens": 100}
    assert billing.settled_charge(auto, {**tokens, "cost": 0.0123}) == (12300, "provider")
    # Token counts cannot be priced when the routed model is unknown: no charge basis.
    assert billing.settled_charge(auto, tokens) is None
    assert billing.settled_charge(auto, {}) is None and billing.settled_charge(auto, None) is None
    # Concrete models keep the tariff fallback.
    assert billing.settled_charge(concrete, tokens) == (210, "tariff")
