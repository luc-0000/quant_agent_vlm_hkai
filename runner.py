"""LLM tool-calling runner — main.py 只需调 run(prompt)。

Tool 注册直接读 skills/hk_ai 里函数的 signature + docstring，无需维护额外 dict。
"""
import inspect
import json
import os

from openai import OpenAI

from skills import hk_ai

# 暴露给 LLM 的工具白名单（其余函数如 call_mcp_tool / get_mcp_endpoint 不暴露）
_TOOL_NAMES = [
    "list_selectable_stocks", "get_quote_by_symbols", "get_market_status",
    "get_stock_kline", "get_account_snapshot", "get_positions", "get_holdings",
    "buy_stock", "sell_stock",
    "get_orders_history", "get_buy_list", "get_sell_list",
    "get_settlement_list", "get_balance_log", "get_fee_log",
    "get_competition_rules",
]

_PY_TYPE_TO_JSON = {
    str: "string", int: "integer", float: "number",
    bool: "boolean", list: "array", dict: "object",
}


def _build_tool_spec(name: str) -> dict:
    """从函数 signature + docstring 自动生成 OpenAI tool spec。"""
    func = getattr(hk_ai, name)
    sig = inspect.signature(func)
    properties, required = {}, []
    for pname, param in sig.parameters.items():
        ann = param.annotation if param.annotation is not inspect.Parameter.empty else str
        properties[pname] = {"type": _PY_TYPE_TO_JSON.get(ann, "string")}
        if param.default is inspect.Parameter.empty:
            required.append(pname)
    # description 取 docstring 第一行（简洁）
    desc = (func.__doc__ or name).strip().split("\n")[0]
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": desc,
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }


TOOLS = [_build_tool_spec(n) for n in _TOOL_NAMES]
_TOOL_FUNCS = {n: getattr(hk_ai, n) for n in _TOOL_NAMES}

MAX_TURNS = 12

_SYSTEM_PROMPT = (
    "你是港股模拟炒股大赛的交易助手。通过调用工具完成用户任务。"
    "每次给买卖指令前必须先用 get_account_snapshot 看可用资金、用 get_positions 看持仓。"
    "买卖数量必须是 10 的整数倍，单笔不超 HK$500,000。回答用中文，简洁清晰。"
)


def _execute_tool(name: str, args: dict) -> dict:
    func = _TOOL_FUNCS.get(name)
    if not func:
        return {"success": False, "error": f"未知工具: {name}"}
    try:
        return func(**args)
    except Exception as e:
        return {"success": False, "error": f"{type(e).__name__}: {str(e)}"}


def _print_env_status() -> None:
    print("=== Pod Env Status ===")
    print(f"  HKAI_MCP_TOKEN:    {'✓ set' if os.getenv('HKAI_MCP_TOKEN') else '✗ MISSING'}")
    print(f"  OPENAI_BASE_URL:   {os.getenv('OPENAI_BASE_URL') or '✗ MISSING'}")
    print(f"  OPENAI_API_KEY:    {'✓ set' if os.getenv('OPENAI_API_KEY') else '✗ MISSING'}")
    print(f"  LLM_MODEL:         {os.getenv('LLM_MODEL', '(default: gpt-4o-mini)')}")
    print(f"  LLM_API_PARAMS:    {os.getenv('LLM_API_PARAMS') or '(empty — using defaults)'}")
    print()


def run(prompt: str) -> None:
    _print_env_status()

    client = OpenAI()
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    try:
        api_params = json.loads(os.getenv("LLM_API_PARAMS") or "{}")
    except json.JSONDecodeError as e:
        print(f"⚠️  LLM_API_PARAMS 解析失败 ({e})，用空 dict 兜底")
        api_params = {}

    messages = [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]

    print(f"=== 任务 ===\n{prompt}\n")

    for turn in range(1, MAX_TURNS + 1):
        try:
            resp = client.chat.completions.create(
                model=model, messages=messages, tools=TOOLS, **api_params,
            )
        except Exception as e:
            # 不打 {e} —— OpenAI SDK 401 异常 message 含部分 API key（sk-xxx...）
            print(f"\n❌ LLM API 调用失败 (turn {turn}): {type(e).__name__}")
            return

        msg = resp.choices[0].message
        finish_reason = resp.choices[0].finish_reason
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            content = msg.content or ""
            # 推理模型（DeepSeek-V4-Pro、GLM-5.2 等）可能把 token 预算全花在
            # reasoning_content 上，content 为空。fallback 到 reasoning_content。
            reasoning = getattr(msg, "reasoning_content", None)
            if not content and reasoning:
                content = reasoning

            print(f"\n=== LLM 最终回答 (finish_reason={finish_reason}) ===")
            if content:
                print(content)
            else:
                print(f"⚠️  模型返回空回答（finish_reason={finish_reason}）。"
                      f"可能是 max_tokens 太小导致推理内容耗尽了 token 预算。")
            return

        for tc in msg.tool_calls:
            name = tc.function.name
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            print(f"\n[turn {turn}] {name}({args}) [finish_reason={finish_reason}]")
            result = _execute_tool(name, args)
            preview = json.dumps(result, ensure_ascii=False)
            print(f"         → {preview[:300]}{'…' if len(preview) > 300 else ''}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False),
            })

        if finish_reason == "length":
            print(f"\n⚠️  turn {turn} 达到 max_tokens 上限，回答可能被截断。")

    print(f"\n⚠️  达到最大轮数 ({MAX_TURNS}) 仍未给出最终答案。")
