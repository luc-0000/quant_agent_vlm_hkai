import sys
import shutil
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from mcp_servers.tech_mcp_servers.tech_tools_mcp import get_tech_tools_mcp_async
import asyncio
from common.consts import Agents
from trading_agents.common.utils import Action, output_results, PositionSignal
from trading_agents.quant_agent_vlm.src.analyzer import WebTradingAnalyzer
from dotenv import load_dotenv

load_dotenv()


async def qa_main(stock_code: str) -> Action:
    tech_client = None
    try:
        tech_client, tech_tools = await get_tech_tools_mcp_async()
        analyzer = WebTradingAnalyzer(tech_tools)

        df = analyzer.fetch_hk_kline_data(stock_code, period="1d", limit=60)
        if df.empty:
            print("Error: No kline data available")
            return Action.HOLD

        results = await analyzer.run_analysis(df, stock_code, "1d")
        formatted_results = analyzer.extract_analysis_results(results)
        final_decision = formatted_results.get('final_decision', {}).get('decision')
        position_signal = extract_decision(final_decision)
        compatible_action = position_signal.to_action()
        if formatted_results.get('final_decision'):
            formatted_results['final_decision']['compatible_action'] = compatible_action.value

        output_path = Path('log/reports')
        output_results(formatted_results, stock_code, output_path, Agents.quant_agent)

        # Copy chart images into reports dir so pod's /api/reports/zip picks them up
        data_dir = project_root / 'data'
        for chart in ['kline_chart.png', 'trend_graph.png']:
            src = data_dir / chart
            if src.exists():
                shutil.copy2(src, output_path / chart)
                print(f'Copied {chart} to reports/')

        print(f'Position signal: {position_signal}')
        print(f'Execution action: {compatible_action}')
        return compatible_action
    except Exception as e:
        print(f"Error: {e}")
        return Action.HOLD
    finally:
        if tech_client is not None:
            del tech_client
        import gc
        gc.collect()


def extract_decision(decision: str) -> PositionSignal:
    if decision == 'LONG':
        return PositionSignal.LONG
    elif decision == 'SHORT':
        return PositionSignal.SHORT
    else:
        return PositionSignal.HOLD


if __name__ == '__main__':
    asyncio.run(qa_main('00700.HK'))
