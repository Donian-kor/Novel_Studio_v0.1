from __future__ import annotations

try:
    import keyring
except Exception:
    keyring = None

from .providers import (
    AnthropicProvider,
    GeminiProvider,
    LMStudioProvider,
    OpenAICompatibleProvider,
)


class ProviderManager:
    IDS = {
        "lmstudio": "LM Studio",
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "gemini": "Google Gemini",
        "openai_compatible": "OpenAI Compatible",
    }
    SERVICE = "NovelStudio"

    def __init__(self, settings):
        self.settings = settings

    def key(self, provider_id: str) -> str:
        if not keyring:
            return ""
        try:
            return keyring.get_password(self.SERVICE, provider_id) or ""
        except Exception:
            return ""

    def save_key(self, provider_id: str, value: str) -> None:
        if not keyring:
            if value:
                raise RuntimeError("keyring 패키지가 필요합니다.")
            return
        if value:
            keyring.set_password(self.SERVICE, provider_id, value)
            return
        try:
            keyring.delete_password(self.SERVICE, provider_id)
        except Exception:
            pass

    def config(self, provider_id: str | None = None) -> dict:
        pid = provider_id or self.settings.data["active_provider"]
        config = dict(self.settings.data.setdefault("providers", {}).get(pid, {}))
        config["api_key"] = self.key(pid)
        return config

    def _build(self, provider_id: str, config: dict):
        if provider_id == "lmstudio":
            return LMStudioProvider(config)
        if provider_id == "anthropic":
            return AnthropicProvider(config)
        if provider_id == "gemini":
            return GeminiProvider(config)
        return OpenAICompatibleProvider(config)

    def build_unsaved(self, provider_id: str, base_url: str, model: str, api_key: str):
        return self._build(
            provider_id,
            {"base_url": base_url, "model": model, "api_key": api_key},
        )

    def provider(self, provider_id: str | None = None):
        pid = provider_id or self.settings.data["active_provider"]
        return self._build(pid, self.config(pid))

    def set_active(self, provider_id: str) -> None:
        if provider_id not in self.IDS:
            raise ValueError(f"지원하지 않는 Provider: {provider_id}")
        self.settings.data["active_provider"] = provider_id
        self.settings.save()

    def set_config(self, provider_id: str, config: dict) -> None:
        self.save_provider(
            provider_id,
            str(config.get("base_url", "")),
            str(config.get("model", "")),
            str(config.get("api_key", "")),
        )

    def save_provider(self, provider_id: str, base_url: str, model: str, api_key: str) -> None:
        providers = self.settings.data.setdefault("providers", {})
        item = providers.setdefault(provider_id, {})
        item["base_url"] = base_url
        item["model"] = model
        self.save_key(provider_id, api_key)
        self.settings.save()
