import json
import os

_platform_key = os.getenv("OPENAI_API_KEY", "")
_platform_url = os.getenv("OPENAI_BASE_URL", "")
_platform_model = os.getenv("LLM_MODEL", "")
_platform_params = {}
try:
    _platform_params = json.loads(os.getenv("LLM_API_PARAMS", "{}"))
except json.JSONDecodeError:
    pass

_local_key = os.getenv("DASHSCOPE_API_KEY", "")

DEFAULT_CONFIG = {
    "model": _platform_model or "qwen3-vl-plus",
    "api_key": _platform_key or _local_key,
    "base_url": _platform_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "temperature": 0.0,
    "max_token": _platform_params.get("max_tokens", 4096),
}
