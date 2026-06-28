"""
Agent for technical indicator analysis in high-frequency trading (HFT) context.
Uses LLM and MCP tools to compute and interpret indicators like MACD, RSI, ROC, Stochastic, and Williams %R.
"""
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
import json


def create_indicator_agent(llm, tech_tools):
    """
    Create an indicator analysis agent node for HFT. The agent uses LLM and MCP indicator tools to analyze OHLCV data.

    Args:
        llm: Language model for analysis
        tech_tools: List of MCP tools (StructuredTool objects)
    """
    async def indicator_agent_node(state):
        # tech_tools 已经是筛选过的工具列表
        selected_tools = tech_tools

        messages = state["messages"]

        indicator_results = {}
        for call in selected_tools:
            tool_name = call.name
            tool_args = {
                "kline_data": state["kline_data"]
            }
            tool_result = await call.ainvoke(tool_args)
            indicator_results[tool_name] = json.dumps(tool_result)
            messages.append(
                AIMessage(content=json.dumps(tool_result))
            )

        time_frame = state['time_frame']
        messages = state["messages"]
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a high-frequency trading (HFT) analyst assistant operating under time-sensitive conditions. "
                    "You must analyze technical indicators to support fast-paced trading execution.\n\n"
                    f"⚠️ The OHLC data provided is from a {time_frame} intervals, reflecting recent market behavior. "
                    "You must interpret this data quickly and accurately.\n\n"
                    "Here is the OHLC data:\n{kline_data}.\n\n"
                    "Call necessary tools, and analyze the results.\n"
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            kline_data=json.dumps(state["kline_data"], indent=2)
        )


        chain = prompt | llm
        final_response = chain.invoke(messages)

        return {
            "messages": messages + [final_response],
            "indicator_report": final_response.content,
        }

    return indicator_agent_node
