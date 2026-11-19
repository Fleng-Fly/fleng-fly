"""OpenRouter transport only. No database, user identity or learning mutations."""

import json
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.core.config import Settings
from app.core.errors import ApiError
from app.modules.ai.billing import AUTO_ROUTER


@dataclass
class Completion:
    content: str
    model: str
    usage: dict = field(default_factory=dict)


class Provider(Protocol):
    async def complete(self, messages: list[dict], schema: dict | None = None) -> Completion: ...
    def stream(self, messages: list[dict]) -> AsyncGenerator[Completion, None]: ...


class NotBilled(ApiError):
    """The provider certainly did not generate: the cost reservation may be released.

    Raised only before the request is sent or when the connection was never
    established. Timeouts, 5xx, broken streams and invalid bodies stay plain
    ApiError: the upstream model may have run, so the reservation is kept.
    """


class UpstreamRefused(NotBilled):
    """OpenRouter answered with a 4xx/429 refusal: no completion was generated.

    OpenRouter documents that prompt processing may still be charged when no
    content is generated, so the prompt cost stays booked (output cost is freed).
    """


def unavailable() -> ApiError:
    return ApiError(503, "AI_UNAVAILABLE", "AI service is unavailable")


def not_billed_unavailable() -> NotBilled:
    return NotBilled(503, "AI_UNAVAILABLE", "AI service is unavailable")


def refused_unavailable() -> UpstreamRefused:
    return UpstreamRefused(503, "AI_UNAVAILABLE", "AI service is unavailable")


def priced(settings: Settings) -> bool:
    """Spending is allowed only for one fixed model with an operator-declared tariff.

    OpenRouter meta-routers (openrouter/auto and friends) pick the model at request
    time, and :online adds per-request search fees; neither has a price we can bound
    before sending, so they are refused rather than treated as free.
    """
    return (
        settings.ai_input_price_per_mtok_usd is not None
        and settings.ai_output_price_per_mtok_usd is not None
        and model_supported(settings)
    )


def model_supported(settings: Settings) -> bool:
    """Concrete models, or exactly `openrouter/auto` when the operator opted in.

    For the Auto Router the configured prices are a ceiling (see Settings.ai_allow_auto_router).
    Every other `openrouter/*` router and `:online` models stay refused.
    """
    model = settings.openrouter_model
    if model == AUTO_ROUTER:
        return settings.ai_allow_auto_router
    return not model.startswith("openrouter/") and not model.endswith(":online")


def unavailable_reason(settings: Settings) -> str | None:
    """Why AI is not usable, as a non-secret code for operators (None when it is ready).

    Mirrors OpenRouterProvider.validate(), but names the first missing requirement so a
    misconfigured deployment is diagnosable from GET /ai/status without exposing any value.
    """
    if not settings.ai_enabled:
        return "disabled"
    if not settings.openrouter_api_key.get_secret_value():
        return "missing_api_key"
    if not settings.openrouter_model:
        return "missing_model"
    if not model_supported(settings):
        return (
            "auto_router_not_enabled"
            if settings.openrouter_model == AUTO_ROUTER
            else "unsupported_model"
        )
    if not priced(settings):
        return "missing_pricing"
    return None


class OpenRouterProvider:
    def __init__(self, settings: Settings, transport: httpx.AsyncBaseTransport | None = None):
        self.settings = settings
        self.transport = transport

    def validate(self) -> None:
        s = self.settings
        if (
            not s.ai_enabled
            or not s.openrouter_api_key.get_secret_value()
            or not s.openrouter_model
            or not priced(s)
        ):
            raise not_billed_unavailable()

    def payload(
        self, messages: list[dict], schema: dict | None = None, stream: bool = False
    ) -> dict:
        self.validate()
        data = {
            "model": self.settings.openrouter_model,
            "messages": messages,
            "max_tokens": self.settings.ai_max_output_tokens,
            "stream": stream,
            # Never route to an endpoint pricier than the tariff used for reservations.
            "provider": {"max_price": max_price(self.settings)},
        }
        if schema and self.settings.ai_structured_outputs:
            data["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "educational_response",
                    "strict": True,
                    "schema": strict_schema(schema),
                },
            }
        return data

    def served_model(self, data: object) -> str:
        """Model recorded for the answer: for the Auto Router, the model OpenRouter routed to.

        Only a short identifier-shaped string is accepted; anything else falls back to the
        configured id. Informational (audit); billing never depends on it.
        """
        configured = self.settings.openrouter_model
        if configured != AUTO_ROUTER or not isinstance(data, dict):
            return configured
        routed = data.get("model")
        if isinstance(routed, str) and re.fullmatch(
            r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.:/-]{1,100}", routed
        ):
            return routed[:150]
        return configured

    def client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.settings.openrouter_base_url + "/",
            headers={
                "Authorization": "Bearer " + self.settings.openrouter_api_key.get_secret_value()
            },
            timeout=self.settings.ai_request_timeout,
            transport=self.transport,
            follow_redirects=False,
        )

    @staticmethod
    def check(response: httpx.Response) -> None:
        if response.status_code == 429:
            raise UpstreamRefused(
                429,
                "AI_RATE_LIMITED",
                "AI provider rate limit reached",
                headers={"Retry-After": "60"},
            )
        if 400 <= response.status_code < 500 and response.status_code != 408:
            # Refused before generation (auth, credits, price filter, validation).
            # Never reflect provider bodies: they can contain input or credential details.
            raise refused_unavailable()
        if response.status_code >= 400:
            raise unavailable()

    async def complete(self, messages: list[dict], schema: dict | None = None) -> Completion:
        payload = self.payload(messages, schema)
        try:
            async with self.client() as client:
                async with client.stream("POST", "chat/completions", json=payload) as response:
                    self.check(response)
                    chunks = bytearray()
                    async for chunk in response.aiter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > self.settings.ai_max_response_chars * 8 + 65536:
                            raise ApiError(
                                502, "AI_INVALID_RESPONSE", "AI response exceeded limits"
                            )
            data = json.loads(chunks)
            if not isinstance(data, dict):
                raise ValueError("Invalid response object")
            choice = data["choices"][0]
            if not isinstance(choice, dict) or not isinstance(choice.get("message"), dict):
                raise ValueError("Invalid choice")
            if data.get("error") or choice.get("finish_reason") != "stop":
                raise ValueError("Incomplete response")
            content = choice["message"]["content"]
            if (
                not isinstance(content, str)
                or not content.strip()
                or len(content) > self.settings.ai_max_response_chars
            ):
                raise ValueError("Invalid content")
            return Completion(content, self.served_model(data), safe_usage(data.get("usage")))
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            # No connection means the request body never reached OpenRouter.
            raise not_billed_unavailable() from exc
        except httpx.TimeoutException as exc:
            raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc
        except httpx.HTTPError as exc:
            raise unavailable() from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ApiError(502, "AI_INVALID_RESPONSE", "Invalid AI response") from exc
        except ApiError:
            raise
        except Exception:
            # Unexpected transport errors may contain credentials; never log/reflect them.
            raise unavailable() from None

    async def stream(self, messages: list[dict]) -> AsyncGenerator[Completion, None]:
        payload = self.payload(messages, stream=True)
        try:
            async with self.client() as client:
                async with client.stream("POST", "chat/completions", json=payload) as response:
                    self.check(response)
                    buffer: list[str] = []
                    size = total = 0
                    finished = False
                    async for line in response.aiter_lines():
                        if line.startswith(":"):
                            continue
                        if line:
                            if line.startswith("data:"):
                                value = line[5:].lstrip(" ")
                                size += len(value)
                                if size > 65536:
                                    raise ValueError("Oversized event")
                                buffer.append(value)
                            continue
                        if not buffer:
                            continue
                        event = "\n".join(buffer)
                        buffer, size = [], 0
                        if event == "[DONE]":
                            if not finished or not total:
                                raise ValueError("Incomplete stream")
                            return
                        data = json.loads(event)
                        if not isinstance(data, dict):
                            raise ValueError("Invalid stream event")
                        if data.get("error"):
                            raise ValueError("Provider stream error")
                        choices = data.get("choices", [])
                        content = ""
                        if choices:
                            choice = choices[0]
                            if not isinstance(choice, dict) or not isinstance(
                                choice.get("delta", {}), dict
                            ):
                                raise ValueError("Invalid delta object")
                            reason = choice.get("finish_reason")
                            if reason and reason != "stop":
                                raise ValueError("Incomplete generation")
                            finished = finished or reason == "stop"
                            content = choice.get("delta", {}).get("content") or ""
                        if not isinstance(content, str):
                            raise ValueError("Invalid delta")
                        total += len(content)
                        if total > self.settings.ai_max_response_chars:
                            raise ValueError("Response too long")
                        yield Completion(
                            content, self.served_model(data), safe_usage(data.get("usage"))
                        )
                    raise ValueError("Stream ended without DONE")
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            # No connection means the request body never reached OpenRouter.
            raise not_billed_unavailable() from exc
        except httpx.TimeoutException as exc:
            raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc
        except httpx.HTTPError as exc:
            raise unavailable() from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ApiError(502, "AI_INCOMPLETE_STREAM", "AI stream did not complete") from exc
        except ApiError:
            raise
        except Exception:
            raise unavailable() from None


def safe_usage(value: object) -> dict:
    if not isinstance(value, dict):
        return {}
    return {
        key: val
        for key, val in value.items()
        if key in {"prompt_tokens", "completion_tokens", "total_tokens", "cost"}
        and isinstance(val, (int, float))
        and not isinstance(val, bool)
        and 0 <= val <= 1e12
    }


def max_price(settings: Settings) -> dict:
    """OpenRouter provider.max_price, in USD per million tokens."""
    return {
        "prompt": float(settings.ai_input_price_per_mtok_usd or 0),
        "completion": float(settings.ai_output_price_per_mtok_usd or 0),
        # Per-request fees are not part of the reservation, so refuse endpoints with them.
        "request": 0,
    }


def get_provider(settings: Settings) -> Provider:
    provider = OpenRouterProvider(settings)
    provider.validate()
    return provider


def strict_schema(schema: dict) -> dict:
    """Constrain all fields when the operator opts into JSON Schema support."""
    import copy

    result = copy.deepcopy(schema)

    def visit(value):
        if isinstance(value, dict):
            if value.get("type") == "object":
                value["additionalProperties"] = False
                value["required"] = list(value.get("properties", {}))
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(result)
    return result
