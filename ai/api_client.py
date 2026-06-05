from dataclasses import dataclass

import requests


class APIClientError(Exception):
    """Raised when an OpenAI-compatible API request fails."""


@dataclass
class OpenAICompatibleClient:
    base_url: str
    api_key: str
    timeout: int = 240

    def _chat_completions_url(self) -> str:
        clean_url = self.base_url.rstrip("/")
        if clean_url.endswith("/chat/completions"):
            return clean_url
        if clean_url.endswith("/v1"):
            return f"{clean_url}/chat/completions"
        return f"{clean_url}/v1/chat/completions"

    def generate(self, model: str, prompt: str) -> str:
        if not self.base_url.strip():
            raise APIClientError("请填写 API Base URL，例如：https://api.openai.com/v1")
        if not self.api_key.strip():
            raise APIClientError("请填写 API Key。")

        headers = {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "你是 PPTer，一个严谨的中文课件学习助手，只根据用户提供的课件内容生成复习材料。",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        try:
            response = requests.post(
                self._chat_completions_url(),
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.HTTPError as exc:
            detail = response.text[:500] if "response" in locals() else ""
            raise APIClientError(f"API 请求失败：{exc}。{detail}") from exc
        except requests.RequestException as exc:
            raise APIClientError(f"无法连接 API 服务，请检查 Base URL 和网络：{exc}") from exc
        except ValueError as exc:
            raise APIClientError("API 返回了无法解析的 JSON 响应。") from exc

        try:
            message = data["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise APIClientError("API 响应格式不符合 OpenAI Chat Completions 兼容格式。") from exc

        if not message:
            raise APIClientError("API 没有返回有效内容，请尝试换模型或缩短输入。")
        return message
