import os
# DEFAULT_CONFIG = {
#     "agent_llm_model": "gpt-4o-mini",
#     "graph_llm_model": "gpt-4o",
#     "agent_llm_temperature": 0.1,
#     "graph_llm_temperature": 0.1,
#     "api_key": "",
# }
# DEFAULT_CONFIG = {
#     "agent_llm_model": "deepseek-chat",
#     "graph_llm_model": "deepseek-chat",
#     "agent_llm_temperature": 1.0,
#     "graph_llm_temperature": 1.0,
#     "api_key": "sk-45698fd966454b8787bd9b1516cfa008",
#     "max_token": 4096,
#     "base_url": "https://api.deepseek.com"
# }

# DEFAULT_CONFIG = {
#     "agent_llm_model": "kimi-k2-0905-preview",
#     "graph_llm_model": "kimi-k2-0905-preview",
#     "agent_llm_temperature": 0.0,
#     "graph_llm_temperature": 0.0,
#     "api_key": "sk-WOvSiozMuzyPffG9ghA7KoLGVEtMYPCeOM7u5vb4YlhdonIU",
#     "max_token": 20000,
#     "base_url": "https://api.moonshot.cn/v1"
# }

DEFAULT_CONFIG = {
    "agent_llm_model": "qwen-plus-latest",
    "graph_llm_model": "qwen3-vl-plus",
    "agent_llm_temperature": 0.0,
    "graph_llm_temperature": 0.0,
    "api_key": os.getenv("DASHSCOPE_API_KEY", ""),
    "max_token": 4096,
    "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
}
