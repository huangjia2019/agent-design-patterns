"""Shared model configuration for all tutorial notebooks.

Usage in notebooks:
    from model_config import get_model
    model = get_model()

Reads from root .env — see .env.example for all options.
Default: ernie provider + ernie-5.1 via AI Studio.
"""
from __future__ import annotations

import os

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # pragma: no cover - exercised in a subprocess test
    load_dotenv = None

try:
    from langchain_dev_utils.chat_models import load_chat_model, register_model_provider
except ModuleNotFoundError:  # pragma: no cover - exercised in a subprocess test
    load_chat_model = None
    register_model_provider = None

_providers_registered = False


def _load_env() -> None:
    """Find .env by walking up from cwd."""
    if load_dotenv is None:
        return

    for candidate in [".env", "../.env", "../../.env", "../../../.env"]:
        load_dotenv(candidate, override=False)


def _register_providers() -> None:
    """Register OpenAI-compatible CN providers not built into init_chat_model.
    Idempotent — safe to call multiple times.

    Uses langchain-dev-utils register_model_provider with chat_model="openai-compatible"
    to create a provider that wraps BaseChatOpenAI with a custom base_url.
    See: https://tbice123123.github.io/langchain-dev-utils/zh/getting-started-guide/chat/
    """
    global _providers_registered
    if _providers_registered:
        return
    if register_model_provider is None:
        return

    # Ernie (AI Studio) — OpenAI-compatible endpoint
    base_url = os.getenv("OPENAI_BASE_URL", "https://aistudio.baidu.com/llm/lmapi/v3")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        return

    os.environ.setdefault("ERNIE_API_KEY", openai_api_key)
    register_model_provider(
        provider_name="ernie",
        chat_model="openai-compatible",
        base_url=base_url,
    )
    _providers_registered = True


def get_model(temperature: float = 0):
    """Load the configured LLM, or return None if no API key is set.

    Env vars:
      MODEL_PROVIDER  — "ernie" (default), "openai", "anthropic", ...
      MODEL_NAME      — "ernie-5.1" (default), "gpt-4o-mini", ...

    For custom providers (ernie, vllm, etc.), register_model_provider creates
    the provider, then load_chat_model resolves it. For built-in providers
    (openai, anthropic), load_chat_model falls through to init_chat_model.
    """
    _load_env()
    _register_providers()

    provider = os.getenv("MODEL_PROVIDER", "ernie")
    model_name = os.getenv("MODEL_NAME", "ernie-5.1")

    key_map = {
        "ernie": "OPENAI_API_KEY",
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    required_key = key_map.get(provider, f"{provider.upper()}_API_KEY")
    if not os.getenv(required_key):
        print(f"No API key found ({required_key}). See .env.example for setup.")
        return None
    if load_chat_model is None:
        print("LangChain model dependencies not installed. Install with `pip install -e '.[langgraph]'`.")
        return None

    model = load_chat_model(f"{provider}:{model_name}", temperature=temperature)
    print(f"Model: {provider}:{model_name}")
    return model
