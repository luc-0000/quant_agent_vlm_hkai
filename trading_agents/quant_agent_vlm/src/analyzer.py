import json
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from skills.hk_ai.trading_api import get_stock_kline
from trading_agents.quant_agent_vlm.src.trading_graph import TradingGraph


class WebTradingAnalyzer:
    def __init__(self, mcp_tools):
        self.trading_graph = TradingGraph()
        self.data_dir = Path("data")
        self.debug = True
        self.mcp_tools = mcp_tools
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def fetch_hk_kline_data(self, symbol: str, period: str = "1d", limit: int = 60) -> pd.DataFrame:
        result = get_stock_kline(symbol, period=period, limit=limit)
        if not result.get("success"):
            print(f"HK AI kline error: {result.get('error')}")
            return pd.DataFrame()

        data = result.get("data", {})

        # Unwrap nested data payloads
        kline = None
        if isinstance(data, dict):
            kline = data.get("kline") or data.get("data", {}).get("kline")
        if isinstance(data, list):
            kline = data

        if not kline:
            print(f"Unexpected kline response shape: {json.dumps(data, ensure_ascii=False)[:500]}")
            return pd.DataFrame()

        df = pd.DataFrame(kline)
        if df.empty:
            return df

        column_mapping = {
            "date": "Datetime",
            "time": "Datetime",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
        existing = {old: new for old, new in column_mapping.items() if old in df.columns}
        df = df.rename(columns=existing)

        for col in ["Datetime", "Open", "High", "Low", "Close"]:
            if col not in df.columns:
                print(f"Missing column: {col}, available: {list(df.columns)}")
                return pd.DataFrame()

        df = df[["Datetime", "Open", "High", "Low", "Close"]]
        df["Datetime"] = pd.to_datetime(df["Datetime"])
        print(f"Fetched {len(df)} kline bars for {symbol} ({period})")
        return df

    async def run_analysis(self, df: pd.DataFrame, asset_name: str, timeframe: str) -> Dict[str, Any]:
        try:
            print(f"DataFrame columns: {df.columns}")
            print(f"DataFrame shape: {df.shape}")

            df_slice = df.tail(49).iloc[:-3] if len(df) > 49 else df.tail(45)

            required_columns = ["Datetime", "Open", "High", "Low", "Close"]
            if not all(col in df_slice.columns for col in required_columns):
                return {
                    "success": False,
                    "error": f"Missing required columns. Available: {list(df_slice.columns)}"
                }

            df_slice = df_slice.reset_index(drop=True)

            df_slice_dict = {}
            for col in required_columns:
                if col == 'Datetime':
                    df_slice_dict[col] = df_slice[col].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
                else:
                    df_slice_dict[col] = df_slice[col].tolist()

            display_timeframe = timeframe
            if timeframe.endswith('h'):
                display_timeframe += 'our'
            elif timeframe.endswith('m'):
                display_timeframe += 'in'
            elif timeframe.endswith('d'):
                display_timeframe += 'ay'

            initial_state = {
                "kline_data": df_slice_dict,
                "analysis_results": None,
                "messages": [],
                "time_frame": display_timeframe,
                "stock_name": asset_name
            }

            self.trading_graph.set_graph_with_tools(self.mcp_tools)
            final_state = await self.trading_graph.graph.ainvoke(initial_state)

            return {
                "success": True,
                "final_state": final_state,
                "asset_name": asset_name,
                "timeframe": display_timeframe,
                "data_length": len(df_slice)
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_analysis_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        if not results.get("success"):
            return {"error": results.get("error")}

        final_state = results["final_state"]

        technical_indicators = final_state.get("indicator_report", "")
        pattern_analysis = final_state.get("pattern_report", "")
        trend_analysis = final_state.get("trend_report", "")
        final_decision_raw = final_state.get("final_trade_decision", "")

        pattern_chart = final_state.get("pattern_image", "")
        trend_chart = final_state.get("trend_image", "")
        pattern_image_filename = final_state.get("pattern_image_filename", "")
        trend_image_filename = final_state.get("trend_image_filename", "")

        final_decision = ""
        if final_decision_raw:
            try:
                start = final_decision_raw.find('{')
                end = final_decision_raw.rfind('}') + 1
                if start != -1 and end != 0:
                    json_str = final_decision_raw[start:end]
                    decision_data = json.loads(json_str)
                    final_decision = {
                        "decision": decision_data.get('decision', 'N/A'),
                        "risk_reward_ratio": decision_data.get('risk_reward_ratio', 'N/A'),
                        "forecast_horizon": decision_data.get('forecast_horizon', 'N/A'),
                        "justification": decision_data.get('justification', 'N/A')
                    }
                else:
                    final_decision = {"raw": final_decision_raw}
            except json.JSONDecodeError:
                final_decision = {"raw": final_decision_raw}

        return {
            "success": True,
            "asset_name": results["asset_name"],
            "timeframe": results["timeframe"],
            "data_length": results["data_length"],
            "technical_indicators": technical_indicators,
            "pattern_analysis": pattern_analysis,
            "trend_analysis": trend_analysis,
            "pattern_chart": pattern_chart,
            "trend_chart": trend_chart,
            "pattern_image_filename": pattern_image_filename,
            "trend_image_filename": trend_image_filename,
            "final_decision": final_decision
        }
