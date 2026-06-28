"""
TradingGraph: Orchestrates the multi-agent trading system using LangChain and LangGraph.
Both text agents and VLM agents share the same model (must be a vision-capable model).
"""
from langchain_openai import ChatOpenAI
from quant_agent_vlm.default_config import DEFAULT_CONFIG
from quant_agent_vlm.src.graph_setup import SetGraph


class TradingGraph:
    def __init__(self, config=None):
        self.config = config if config is not None else DEFAULT_CONFIG.copy()

        self.agent_llm = ChatOpenAI(
            model=self.config.get("model", "qwen3-vl-plus"),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
            temperature=self.config.get("temperature"),
            max_tokens=self.config.get("max_token"),
            streaming=False
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("model", "qwen3-vl-plus"),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
            temperature=self.config.get("temperature"),
            max_tokens=self.config.get("max_token"),
            streaming=False
        )

    def set_graph_with_tools(self, tech_tools):
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            tech_tools=tech_tools,
        )
        self.graph = self.graph_setup.set_graph()
        return self.graph

    def refresh_llms(self):
        self.agent_llm = ChatOpenAI(
            model=self.config.get("model", "qwen3-vl-plus"),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
            temperature=self.config.get("temperature", 0.0)
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("model", "qwen3-vl-plus"),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),
            temperature=self.config.get("temperature", 0.0)
        )
        self.graph = self.graph_setup.set_graph()
