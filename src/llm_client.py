import os
import json
import time
import requests


class LLMClient:
    def __init__(self, config=None):
        config = config or {}
        self.api_key = config.get('api_key') or os.getenv('OPENAI_API_KEY')
        self.api_base = config.get('api_base') or os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self.model = config.get('model') or os.getenv('OPENAI_MODEL', 'gpt-4-turbo')
        self.provider = config.get('provider') or os.getenv('LLM_PROVIDER', 'openai')
        self.temperature = config.get('temperature', 0.2)
        self.max_retries = config.get('max_retries', 3)
        self.retry_delay = config.get('retry_delay', 2)

        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError("请配置 API Key！在 .env 文件中设置 OPENAI_API_KEY，或通过代码传入 config。")

    def chat(self, system_content, user_content):
        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        last_error = None
        for attempt in range(1, self.max_retries + 1):
            try:
                return self._call_api(messages)
            except Exception as e:
                last_error = e
                print(f"LLM 调用失败 (第 {attempt}/{self.max_retries} 次): {e}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * attempt)

        raise RuntimeError(f"LLM 调用失败: {last_error}")

    def _call_api(self, messages):
        url = self.api_base.rstrip('/') + '/chat/completions'

        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }

        payload = {
            'model': self.model,
            'messages': messages,
            'temperature': self.temperature,
            'max_tokens': 4000
        }

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=120
        )

        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:500]}")

        data = response.json()
        return data['choices'][0]['message']['content']
