"""The ONLY place this project talks to a language model (OpenRouter, OpenAI-compatible API).

Settings come from "Portfolio Projects/.env" (two folders above this repo), then repo/.env,
then normal environment variables:
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_MAIN, MODEL_CHEAP, MODEL_JUDGE
The key is never printed or logged. Tests use FakeClient and never touch the network.
"""

import os
import time
from dataclasses import dataclass

from dotenv import load_dotenv

from olist_analytics.config import REPO_ROOT

ENV_FILES = [REPO_ROOT.parent.parent / ".env", REPO_ROOT / ".env"]
MODEL_VARIABLES = {"main": "MODEL_MAIN", "cheap": "MODEL_CHEAP", "judge": "MODEL_JUDGE"}


@dataclass
class LLMReply:
    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    cost_usd: float | None = None  # OpenRouter reports the cost when usage accounting is on
    latency_s: float | None = None


def load_settings() -> None:
    """Read the .env files without overriding variables that are already set."""
    for env_file in ENV_FILES:
        if env_file.exists():
            load_dotenv(env_file, override=False)


class OpenRouterClient:
    def __init__(self, model_key: str = "cheap"):
        load_settings()
        self.api_key = os.getenv("OPENROUTER_API_KEY", "")
        self.base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
        self.model = os.getenv(MODEL_VARIABLES[model_key], "")
        if not self.api_key or not self.model:
            raise RuntimeError(
                f"OPENROUTER_API_KEY or {MODEL_VARIABLES[model_key]} is not set. "
                "Add them to 'Portfolio Projects/.env', or use --dry-run."
            )

    def complete(self, system: str, user: str) -> LLMReply:
        from openai import OpenAI  # imported here so tests never need it

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        start = time.perf_counter()
        response = client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.2,
            extra_body={"usage": {"include": True}},  # ask OpenRouter to report the cost
        )
        usage = response.usage
        return LLMReply(
            text=response.choices[0].message.content or "",
            model=response.model or self.model,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            cost_usd=getattr(usage, "cost", None),
            latency_s=round(time.perf_counter() - start, 3),
        )


class FakeClient:
    """Offline stand-in for tests and --dry-run. Returns a fixed reply, costs nothing."""

    model = "fake-client (dry run, not a real model)"

    def __init__(self, reply: str):
        self.reply = reply

    def complete(self, system: str, user: str) -> LLMReply:
        return LLMReply(
            text=self.reply,
            model=self.model,
            prompt_tokens=0,
            completion_tokens=0,
            cost_usd=0.0,
            latency_s=0.0,
        )
