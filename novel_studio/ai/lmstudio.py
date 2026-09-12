from __future__ import annotations
import json
import urllib.request
import urllib.error

class LMStudioError(RuntimeError):
    pass

class LMStudioClient:
    def __init__(self, base_url: str = "http://localhost:1234", model: str = ""):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def list_models(self) -> list[dict]:
        try:
            req = urllib.request.Request(self.base_url + "/v1/models", headers={"Accept":"application/json"})
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8")).get("data", [])
        except Exception as exc:
            raise LMStudioError(f"LM Studio 연결 실패: {exc}") from exc

    def chat(self, messages: list[dict], temperature: float = 0.7, top_p: float = 0.9, max_tokens: int = 7000, model: str | None = None) -> str:
        model_id = model or self.model
        if not model_id:
            models = self.list_models()
            if not models:
                raise LMStudioError("LM Studio에 로드된 모델이 없습니다.")
            model_id = models[0].get("id", "")
        payload = {"model": model_id, "messages": messages, "temperature": temperature, "top_p": top_p, "max_tokens": max_tokens, "stream": False}
        try:
            req = urllib.request.Request(self.base_url + "/v1/chat/completions", data=json.dumps(payload, ensure_ascii=False).encode("utf-8"), headers={"Content-Type":"application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=1800) as response:
                data = json.loads(response.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="ignore")
            raise LMStudioError(f"LM Studio HTTP {exc.code}: {detail}") from exc
        except Exception as exc:
            raise LMStudioError(f"AI 요청 실패: {exc}") from exc
