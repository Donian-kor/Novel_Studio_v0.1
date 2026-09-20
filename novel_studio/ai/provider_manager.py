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
        # 정지 버튼과 연동되는 취소 훅. NovelController가 주입한다.
        self.cancel_check = lambda: False
        self._abort_handler = None
        # 마지막으로 만든 provider 인스턴스(진행 중 응답 abort 대상)
        self._active_provider = None

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
            provider = LMStudioProvider(config)
        elif provider_id == "anthropic":
            provider = AnthropicProvider(config)
        elif provider_id == "gemini":
            provider = GeminiProvider(config)
        else:
            provider = OpenAICompatibleProvider(config)
        # 정지 버튼 → 취소 신호가 이 인스턴스로 전달된다.
        provider.cancel_check = self.cancel_check
        provider._abort_handler = self._abort_handler
        self._active_provider = provider
        return provider

    def build_unsaved(self, provider_id: str, base_url: str, model: str, api_key: str):
        return self._build(
            provider_id,
            {"base_url": base_url, "model": model, "api_key": api_key},
        )

    def probe(self, provider_id: str | None = None):
        """연결 자동 확인용 프로바이더를 만든다.

        ``_build``가 등록하는 ``_active_provider``(정지 버튼의 abort 대상)를
        프로브 인스턴스로 덮어쓰지 않도록 즉시 복원한다. 그렇지 않으면 연결
        확인이 진행 중인 AI 작업의 정지(abort) 대상을 바꿔버릴 수 있다.
        """
        pid = provider_id or self.settings.data["active_provider"]
        previous = self._active_provider
        provider = self._build(pid, self.config(pid))
        if self._active_provider is provider:
            self._active_provider = previous
        return provider

    def provider(self, provider_id: str | None = None):
        pid = provider_id or self.settings.data["active_provider"]
        return self._build(pid, self.config(pid))

    def set_active(self, provider_id: str) -> None:
        if provider_id not in self.IDS:
            raise ValueError(f"지원하지 않는 Provider: {provider_id}")
        self.settings.data["active_provider"] = provider_id
        self.settings.save()

    def set_cancel_handler(self, cancel_check, abort_handler=None) -> None:
        """정지 버튼과 취소 훅을 연결한다(NovelController가 호출)."""
        self.cancel_check = cancel_check or (lambda: False)
        self._abort_handler = abort_handler

    def abort(self) -> None:
        """현재 진행 중인 provider의 HTTP 응답을 닫아 I/O를 즉시 중단한다."""
        active = self._active_provider
        if active is not None and hasattr(active, "abort"):
            active.abort()

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
