from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import Settings, get_settings


@dataclass(slots=True)
class LMStudioClient:
  """Thin wrapper around the LM Studio REST API."""

  settings: Settings

  async def generate_reply(self, prompt: str) -> str:
    payload = {
        "model": self.settings.lm_studio_model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": self.settings.lm_temperature,
        "max_tokens": self.settings.lm_max_tokens,
    }

    url = f"{self.settings.lm_studio_url.rstrip('/')}/v1/chat/completions"
    async with httpx.AsyncClient(timeout=self.settings.lm_request_timeout) as client:
      try:
        response = await client.post(url, json=payload)
        response.raise_for_status()
      except httpx.HTTPStatusError as exc:
        details = _extract_error_details(exc.response)
        raise RuntimeError(f"LM Studio returned {exc.response.status_code}: {details}") from exc
      except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to reach LM Studio service: {exc}") from exc

    data = response.json()
    try:
      message = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
      raise RuntimeError("Unexpected payload returned by LM Studio.") from exc

    return message.strip()


def _extract_error_details(response: httpx.Response) -> str:
  try:
    payload: Any = response.json()
  except json.JSONDecodeError:
    return response.text

  if isinstance(payload, dict):
    return payload.get("error", payload)
  return str(payload)


def get_lm_client() -> LMStudioClient:
  return LMStudioClient(settings=get_settings())
