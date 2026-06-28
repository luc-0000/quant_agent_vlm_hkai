import asyncio
import math
import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from trading_agents.quant_agent_vlm.default_config import DEFAULT_CONFIG
from trading_agents.quant_agent_vlm.src.stock_selector import StockSelector
from trading_agents.common.utils import Action

MIN_UNIT = 10
MAX_ORDER_AMOUNT = 500_000


async def main(stock_code: str = None, **kwargs):
    """
    Quant Agent HK AI — full pipeline entry point.
    Called by the fintools agent framework (agent.yml → import_path: main:main).

    Args:
        stock_code: Optional HK stock code (e.g. '00700.HK'). If omitted, LLM picks one.
    """
    if stock_code:
        print(f"Using provided stock: {stock_code}")
    else:
        print("=== Step 1: LLM Stock Selection ===")
        selector_llm = ChatOpenAI(
            model=DEFAULT_CONFIG["agent_llm_model"],
            api_key=DEFAULT_CONFIG["api_key"],
            base_url=DEFAULT_CONFIG["base_url"],
            temperature=0.1,
            max_tokens=1024,
        )
        selector = StockSelector(selector_llm)
        pick = selector.pick_stock()
        stock_code = pick["stock_code"]
        print(f"Selected: {pick['stock_code']} ({pick.get('stock_name', '')})")
        print(f"Reason: {pick.get('reason', '')}")

    print(f"\n=== Step 2: Quant Agent Analysis for {stock_code} ===")
    from trading_agents.quant_agent_vlm.main import qa_main
    action = await qa_main(stock_code)
    print(f"Analysis decision: {action.value.upper()}")

    print(f"\n=== Step 3: Trade Execution ===")
    await _execute_trade(action, stock_code)


async def _execute_trade(action: Action, stock_code: str):
    from skills.hk_ai.trading_api import (
        get_account_snapshot, get_positions, get_quote_by_symbols,
        buy_stock, sell_stock,
    )

    if action == Action.HOLD:
        print("[Execution] HOLD — no trade executed")
        return

    if action == Action.BUY:
        account = get_account_snapshot()
        if not account.get("success"):
            print(f"[Execution] Failed to get account: {account.get('error')}")
            return
        acct_data = _unwrap(account["data"])
        available = acct_data.get("available", 0)
        print(f"[Execution] Available cash: HK$ {available:,.2f}")

        quote = get_quote_by_symbols([stock_code])
        price = 0
        if quote.get("success"):
            qdata = _unwrap(quote["data"])
            if qdata:
                price = qdata[0].get("quote", {}).get("price", 0)
        if not price:
            print(f"[Execution] Failed to get price for {stock_code}")
            return
        print(f"[Execution] {stock_code} price: HK$ {price:,.2f}")

        cash_to_use = min(available * 0.9, MAX_ORDER_AMOUNT)
        raw_qty = int(cash_to_use / price)
        quantity = (raw_qty // MIN_UNIT) * MIN_UNIT
        if quantity < MIN_UNIT:
            print(f"[Execution] Insufficient cash: need HK$ {price * MIN_UNIT:,.2f}, have HK$ {available:,.2f}")
            return

        order_amount = quantity * price
        print(f"[Execution] BUY {stock_code} x {quantity} shares ≈ HK$ {order_amount:,.2f}")
        result = buy_stock(stock_code, quantity)
        _print_trade_result("BUY", result)

    elif action == Action.SELL:
        positions = get_positions()
        if not positions.get("success"):
            print(f"[Execution] Failed to get positions: {positions.get('error')}")
            return
        pos_data = _unwrap(positions["data"])
        holding_qty = 0
        for p in (pos_data or []):
            if isinstance(p, dict) and p.get("stock_code") == stock_code:
                holding_qty = p.get("quantity", 0) or p.get("shares", 0)
                break
        if holding_qty < MIN_UNIT:
            print(f"[Execution] No position in {stock_code} to sell (holding: {holding_qty})")
            return

        quantity = (holding_qty // MIN_UNIT) * MIN_UNIT
        print(f"[Execution] SELL {stock_code} x {quantity} shares")
        result = sell_stock(stock_code, quantity)
        _print_trade_result("SELL", result)


def _unwrap(data):
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        inner = data.get("data", data)
        if isinstance(inner, list):
            return inner
        return data
    return []


def _print_trade_result(side: str, result: dict):
    if result.get("success"):
        d = result.get("data", {})
        if isinstance(d, dict):
            inner = d.get("data", d)
        else:
            inner = d
        order_id = inner.get("order_id", "?")
        price = inner.get("price", "?")
        qty = inner.get("quantity", "?")
        fee = inner.get("fee", "?")
        print(f"[Execution] {side} OK | order_id={order_id} | price={price} | qty={qty} | fee={fee}")
    else:
        print(f"[Execution] {side} FAILED: {result.get('error')}")


if __name__ == '__main__':
    stock = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(main(stock_code=stock))
