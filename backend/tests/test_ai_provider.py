import json

import httpx
import pytest
from app.core.config import Settings
from app.core.errors import ApiError
from app.modules.ai.provider import OpenRouterProvider
from pydantic import ValidationError


def settings(**kwargs):
    return Settings(
        ai_enabled=True, openrouter_api_key="test-only-key", openrouter_model="test/model", **kwargs
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
