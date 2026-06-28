"""
LLM-based stock selector: picks the most promising HK stock from the available list
using market data (quotes, change %) and LLM reasoning.
"""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from skills.hk_ai.trading_api import list_selectable_stocks, get_quote_by_symbols


STOCK_SELECTOR_SYSTEM_PROMPT = """You are a Hong Kong stock selection analyst. Your task is to pick the ONE stock that shows the best short-term trading potential from a list of candidates.

Analyze the provided market data and select based on:
1. Momentum — recent price change %, volume activity
2. Liquidity — sufficient trading volume for easy entry/exit
3. Volatility — enough price movement to generate profit, but not extreme risk

Return ONLY a JSON object (no markdown, no extra text):
{"stock_code": "00700.HK", "stock_name": "Tencent", "reason": "one-line rationale in English"}

Rules:
- Pick exactly ONE stock
- The stock_code must be from the provided list
- Prefer stocks with moderate positive momentum (not already overbought)
- Avoid stocks with extreme gaps or abnormal volume spikes"""


class StockSelector:
    def __init__(self, llm):
        self.llm = llm

    def pick_stock(self) -> dict:
        stocks_result = list_selectable_stocks()
        if not stocks_result.get("success"):
            raise RuntimeError(f"Failed to list stocks: {stocks_result.get('error')}")
        stocks = _unwrap_data(stocks_result["data"])
        if not stocks:
            raise RuntimeError("No selectable stocks available")

        symbols = [s["stock_code"] for s in stocks if s.get("stock_code")]
        quote_result = get_quote_by_symbols(symbols)
        quotes_raw = _unwrap_data(quote_result.get("data", {})) if quote_result.get("success") else []

        market_summary = self._build_market_summary(stocks, quotes_raw)

        messages = [
            SystemMessage(content=STOCK_SELECTOR_SYSTEM_PROMPT),
            HumanMessage(content=market_summary),
        ]
        response = self.llm.invoke(messages)
        return self._parse_response(response.content)

    def _build_market_summary(self, stocks: list, quotes: list) -> str:
        quote_by_symbol = {}
        if quotes:
            for q in quotes:
                if isinstance(q, dict):
                    code = q.get("stock_code", "")
                    price_info = q.get("quote", {})
                    quote_by_symbol[code] = price_info.get("price", "")

        lines = [f"Available HK stocks ({len(stocks)} total):"]
        for s in stocks:
            code = s.get("stock_code", "?")
            name = s.get("stock_name", "")
            price = s.get("latest_price", "N/A")
            change_pct = s.get("changeRate", "")
            quote_price = quote_by_symbol.get(code, "")
            parts = [f"  {code} {name} | price={price}"]
            if change_pct:
                parts.append(f"change={change_pct}%")
            if quote_price and quote_price != price:
                parts.append(f"latest_quote={quote_price}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)

    def _parse_response(self, raw: str) -> dict:
        raw = raw.strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(raw[start:end])
        raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]}")


def _unwrap_data(data):
    """Unwrap nested MCP response: {'code': 0, 'msg': 'ok', 'data': [...]} -> [...]"""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        inner = data.get("data")
        if isinstance(inner, list):
            return inner
        return data
    return []
