import json
import time
from langchain_core.messages import HumanMessage, SystemMessage
from openai import RateLimitError


def invoke_with_retry(call_fn, *args, retries=3, wait_sec=4):
    for attempt in range(retries):
        try:
            return call_fn(*args)
        except RateLimitError:
            print(f"Rate limit hit, retrying in {wait_sec}s (attempt {attempt + 1}/{retries})...")
        except Exception as e:
            print(f"Other error: {e}, retrying in {wait_sec}s (attempt {attempt + 1}/{retries})...")
        if attempt < retries - 1:
            time.sleep(wait_sec)
    raise RuntimeError("Max retries exceeded")


def create_trend_agent(tool_llm, graph_llm, tech_tools):
    async def trend_agent_node(state):
        tool_map = {t.name: t for t in tech_tools}
        trend_tool = tool_map["generate_trend_image"]

        tool_result = await trend_tool.ainvoke({"kline_data": state["kline_data"]})
        if isinstance(tool_result, list) and len(tool_result) > 0:
            tool_result = tool_result[0].get('text')
        trend_image_b64 = json.loads(tool_result).get("trend_image")

        time_frame = state['time_frame']
        messages = [
            SystemMessage(content=(
                "You are a K-line trend pattern recognition assistant operating in a high-frequency trading context. "
                "According to the chart generated, analyze the image for support/resistance trendlines and known candlestick patterns. "
                "Only then should you proceed to make a prediction about the short-term trend (upward, downward, or sideways)."
            )),
            HumanMessage(content=f"Here is the recent kline data:\n{json.dumps(state['kline_data'], indent=2)}")
        ]

        if trend_image_b64:
            image_prompt = [
                {
                    "type": "text",
                    "text": (
                        f"This candlestick ({time_frame} K-line) chart includes automated trendlines: the **blue line** is support, and the **red line** is resistance, both derived from recent closing prices.\n\n"
                        "Analyze how price interacts with these lines — are candles bouncing off, breaking through, or compressing between them?\n\n"
                        "Based on trendline slope, spacing, and recent K-line behavior, predict the likely short-term trend: **upward**, **downward**, or **sideways**. "
                        "Support your prediction with respect to prediction, reasoning, signals."
                    )
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{trend_image_b64}"
                    }
                }
            ]
            final_response = invoke_with_retry(graph_llm.invoke, [
                SystemMessage(content=(
                    "You are a K-line trend pattern recognition assistant operating in a high-frequency trading context. "
                    "Your task is to analyze candlestick charts annotated with support and resistance trendlines."
                )),
                HumanMessage(content=image_prompt)
            ])
        else:
            final_response = invoke_with_retry(tool_llm.invoke, messages)

        return {
            "messages": messages + [final_response],
            "trend_report": final_response.content,
            "trend_image_base64": trend_image_b64
        }

    return trend_agent_node
