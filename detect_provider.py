import sys
import requests

API_KEY = "sk-59457476cc18447da793a7a2ebd98a37"

candidates = [
    {
        "name": "DeepSeek",
        "api_base": "https://api.deepseek.com/v1",
        "test_models": ["deepseek-chat", "deepseek-reasoner"]
    },
    {
        "name": "SiliconFlow",
        "api_base": "https://api.siliconflow.cn/v1",
        "test_models": ["Qwen/Qwen2.5-72B-Instruct", "deepseek-ai/DeepSeek-V3"]
    },
    {
        "name": "OpenAI",
        "api_base": "https://api.openai.com/v1",
        "test_models": ["gpt-4-turbo", "gpt-4o-mini", "gpt-3.5-turbo"]
    },
    {
        "name": "DashScope",
        "api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "test_models": ["qwen-turbo", "qwen-plus"]
    }
]

headers = {
    "Authorization": "Bearer " + API_KEY,
    "Content-Type": "application/json"
}

print("=" * 60)
print("  API Key Provider Detection")
print("=" * 60)
print()

for cand in candidates:
    print("[Testing] " + cand["name"])
    sys.stdout.flush()
    try:
        url = cand["api_base"].rstrip("/") + "/models"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            models = [m["id"] for m in data.get("data", [])]
            print("  [OK] Match found!")
            print("  API_BASE = " + cand["api_base"])
            print("  Available models (first 10):")
            for m in models[:10]:
                print("    - " + m)
            if len(models) > 10:
                print("    ... and " + str(len(models) - 10) + " more")
            print()
            print("=" * 60)
            print("  Recommended .env config:")
            print("  OPENAI_API_KEY=" + API_KEY)
            print("  OPENAI_API_BASE=" + cand["api_base"])
            print("  OPENAI_MODEL=" + (models[0] if models else cand["test_models"][0]))
            print("  LLM_PROVIDER=" + cand["name"])
            print("=" * 60)
            break
        else:
            print("  [FAIL] HTTP " + str(r.status_code))
            try:
                resp_json = r.json()
                print("         " + str(resp_json).replace("\n", " ")[:200])
            except:
                print("         " + r.text[:200])
    except Exception as e:
        print("  [FAIL] " + str(e))
    print()
