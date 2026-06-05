from dataclasses import dataclass

import requests


class OllamaError(Exception):
    """Raised when the local Ollama service cannot complete a request."""


@dataclass
class OllamaClient:
    base_url: str = "http://localhost:11434"
    timeout: int = 240

    def _url(self, path: str) -> str:
        return f"{self.base_url.rstrip('/')}{path}"

    def check_available(self) -> None:
        try:
            response = requests.get(self._url("/api/tags"), timeout=5)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(
                "无法连接本地 Ollama。请确认已安装 Ollama，并已运行：ollama serve"
            ) from exc

    def generate(self, model: str, prompt: str) -> str:
        self.check_available()
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_ctx": 8192,
            },
        }

        try:
            response = requests.post(
                self._url("/api/generate"),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise OllamaError(
                f"Ollama 调用失败，请确认模型已拉取并可运行：ollama pull {model}"
            ) from exc
        except ValueError as exc:
            raise OllamaError("Ollama 返回了无法解析的响应。") from exc

        message = data.get("response", "").strip()
        if not message:
            raise OllamaError("Ollama 没有返回有效内容，请尝试换一个模型或缩短输入。")
        return message
