"""Offline-safe Gemini adapter for the V2.2A qualification experiment only.

It is deliberately not wired into the student runtime.  Credentials are read
only when a caller explicitly invokes ``extract`` in an authorized process.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Callable

from app.models.obligation import ActionType
from app.verification.models import DecomposedUserClaim, TypedUserField

PROMPT_VERSION = "prompt_v1"
SCHEMA_VERSION = "v1"
PROMPT = """Analyze only the supplied Vietnamese user text. Return JSON with claims only.
Do not use outside knowledge, search sources, or decide truth. Preserve claim order and
independent obligation scope. Every non-null field must be copied from a grounded span in
the text. Omit uncertain fields. Never invent a year, amount, or audience. Do not return a verdict.
"""


class ProviderConfigurationError(RuntimeError): pass
class ProviderSchemaError(RuntimeError): pass
class ProviderGroundingError(RuntimeError): pass


def prompt_hash() -> str:
    return sha256(PROMPT.encode()).hexdigest()


def generation_config(types: Any) -> Any:
    """Use Gemini 3.8's model-default sampling; retain JSON-only output."""
    return types.GenerateContentConfig(response_mime_type="application/json")


def runtime_config() -> tuple[str, str]:
    key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("UNITRUST_GEMINI_MODEL")
    if not key or not model or os.getenv("UNITRUST_ALLOW_REAL_PROVIDER_EVAL") != "1":
        raise ProviderConfigurationError("REAL_PROVIDER_CONFIGURATION_REQUIRED")
    return key, model


def _field(text: str, raw: str | None, normalized: str | int | None = None) -> TypedUserField | None:
    if raw is None:
        return None
    start = text.find(raw)
    if start < 0:
        raise ProviderGroundingError("UNGROUNDED_FIELD")
    return TypedUserField(text=raw, raw_text=raw, start_char=start, end_char=start + len(raw), normalized_value=normalized, extraction_method="ai_assisted")


def validate_payload(text: str, payload: dict[str, Any]) -> list[DecomposedUserClaim]:
    if set(payload) - {"claims"} or not isinstance(payload.get("claims"), list):
        raise ProviderSchemaError("INVALID_TOP_LEVEL_SCHEMA")
    claims: list[DecomposedUserClaim] = []
    for index, item in enumerate(payload["claims"]):
        if not isinstance(item, dict) or "verdict" in item:
            raise ProviderSchemaError("TRUST_VERDICT_OR_INVALID_CLAIM")
        claim_text = item.get("claim_text")
        start = text.find(claim_text or "")
        if not claim_text or start < 0:
            raise ProviderGroundingError("UNGROUNDED_CLAIM")
        action_raw = item.get("action")
        action_normalized = item.get("action_normalized")
        if action_normalized is not None and action_normalized not in {a.value for a in ActionType}:
            raise ProviderSchemaError("INVALID_ACTION")
        deadline_raw = item.get("deadline_raw")
        deadline_normalized = item.get("deadline_normalized")
        if deadline_normalized and (not deadline_raw or len(deadline_raw.split("/")) < 3):
            raise ProviderGroundingError("INVENTED_YEAR")
        amount_raw = item.get("amount_raw")
        amount_value = item.get("amount_value")
        if amount_value is not None and not isinstance(amount_value, int):
            raise ProviderSchemaError("INVALID_AMOUNT")
        documents = [_field(text, value) for value in item.get("required_documents", [])]
        claims.append(DecomposedUserClaim(
            claim_id=f"ai-{index + 1}", raw_claim_text=claim_text, start_char=start, end_char=start + len(claim_text),
            extraction_method="ai_assisted", audience=_field(text, item.get("audience")),
            action=_field(text, action_raw, action_normalized), deadline=_field(text, deadline_raw, deadline_normalized),
            amount=_field(text, amount_raw, amount_value), required_documents=[field for field in documents if field],
        ))
    return claims


@dataclass
class GeminiQualificationAdapter:
    transport: Callable[[str, str, str], str] | None = None

    def extract(self, text: str) -> tuple[list[DecomposedUserClaim], float, str]:
        key, model = runtime_config()
        started = time.perf_counter()
        if self.transport:
            raw = self.transport(key, model, text)
        else:
            try:
                from google import genai
                from google.genai import types
            except ImportError as exc:
                raise ProviderConfigurationError("GOOGLE_GENAI_SDK_NOT_INSTALLED") from exc
            client = genai.Client(api_key=key)
            response = client.models.generate_content(
                model=model, contents=f"{PROMPT}\nUSER TEXT:\n{text}",
                config=generation_config(types),
            )
            raw = response.text
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderSchemaError("MALFORMED_JSON") from exc
        return validate_payload(text, payload), (time.perf_counter() - started) * 1000, model
