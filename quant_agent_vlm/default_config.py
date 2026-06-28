import json
import os

# ── Agent LLM (text) ── uses platform-injected env vars, falls back to local DashScope
_platform_key = os.getenv("OPENAI_API_KEY", "")
_platform_url = os.getenv("OPENAI_BASE_URL", "")
_platform_model = os.getenv("LLM_MODEL", "")
_platform_params = {}
try:
    _platform_params = json.loads(os.getenv("LLM_API_PARAMS", "{}"))
except json.JSONDecodeError:
    pass

_local_key = os.getenv("DASHSCOPE_API_KEY", "")

# ── Graph LLM (VLM) ── always DashScope (qwen3-vl-plus requires DashScope)
_graph_key = _local_key or _platform_key
_graph_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

DEFAULT_CONFIG = {
    # Agent (text) LLM
    "agent_llm_model": _platform_model or "qwen-plus-latest",
    "agent_llm_temperature": 0.0,
    "agent_api_key": _platform_key or _local_key,
    "agent_base_url": _platform_url or "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "agent_max_token": _platform_params.get("max_tokens", 4096),

    # Graph (VLM) LLM — always DashScope
    "graph_llm_model": "qwen3-vl-plus",
    "graph_llm_temperature": 0.0,
    "graph_api_key": _graph_key,
    "graph_base_url": _graph_url,
    "graph_max_token": _platform_params.get("max_tokens", 4096),
}
