"""OpenRouter transport only. No database, user identity or learning mutations."""

import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field
from typing import Protocol

import httpx

from app.core.config import Settings
from app.core.errors import ApiError


@dataclass
class Completion:
    content: str
    model: str
    usage: dict = field(default_factory=dict)


class Provider(Protocol):
    async def complete(self, messages: list[dict], schema: dict | None = None) -> Completion: ...
    def stream(self, messages: list[dict]) -> AsyncGenerator[Completion, None]: ...


def unavailable() -> ApiError:
    return ApiError(503, "AI_UNAVAILABLE", "AI service is unavailable")


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
        ):
            raise unavailable()

    def payload(
        self, messages: list[dict], schema: dict | None = None, stream: bool = False
    ) -> dict:
        self.validate()
        data = {
            "model": self.settings.openrouter_model,
            "messages": messages,
            "max_tokens": self.settings.ai_max_output_tokens,
            "stream": stream,
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
            raise ApiError(
                429,
                "AI_RATE_LIMITED",
                "AI provider rate limit reached",
                headers={"Retry-After": "60"},
            )
        if response.status_code >= 400:
            # Never reflect provider bodies: they can contain input or credential details.
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
            choice = data["choices"][0]
            if data.get("error") or choice.get("finish_reason") != "stop":
                raise ValueError("Incomplete response")
            content = choice["message"]["content"]
            if (
                not isinstance(content, str)
                or not content.strip()
                or len(content) > self.settings.ai_max_response_chars
            ):
                raise ValueError("Invalid content")
            return Completion(
                content, self.settings.openrouter_model, safe_usage(data.get("usage"))
            )
        except httpx.TimeoutException as exc:
            raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc
        except httpx.HTTPError as exc:
            raise unavailable() from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ApiError(502, "AI_INVALID_RESPONSE", "Invalid AI response") from exc

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
                        if data.get("error"):
                            raise ValueError("Provider stream error")
                        choices = data.get("choices", [])
                        content = ""
                        if choices:
                            choice = choices[0]
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
                            content, self.settings.openrouter_model, safe_usage(data.get("usage"))
                        )
                    raise ValueError("Stream ended without DONE")
        except httpx.TimeoutException as exc:
            raise ApiError(504, "AI_TIMEOUT", "AI request timed out") from exc
        except httpx.HTTPError as exc:
            raise unavailable() from exc
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ApiError(502, "AI_INCOMPLETE_STREAM", "AI stream did not complete") from exc


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
