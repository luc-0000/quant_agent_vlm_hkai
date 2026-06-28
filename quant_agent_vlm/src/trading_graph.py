"""
TradingGraph: Orchestrates the multi-agent trading system using LangChain and LangGraph.
Initializes LLMs and MCP tools for indicator, pattern, and trend analysis.
Uses lazy loading to avoid deadlock when initializing MCP subprocess.
"""
from langchain_openai import ChatOpenAI
from quant_agent_vlm.default_config import DEFAULT_CONFIG
from quant_agent_vlm.src.graph_setup import SetGraph


class TradingGraph:
    """
    Main orchestrator for the multi-agent trading system.
    Sets up LLMs, toolkits, and agent nodes for indicator, pattern, and trend analysis.
    """
    def __init__(self, config=None):
        # --- Configuration and LLMs ---
        self.config = config if config is not None else DEFAULT_CONFIG.copy()
        
        # Initialize LLMs with config values
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),  # 新版本使用base_url而不是openai_api_base
            temperature=self.config.get("temperature"),
            max_tokens=self.config.get("max_token"),
            streaming=False
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o-mini"),
            api_key=self.config.get("api_key"),
            base_url=self.config.get("base_url"),  # 新版本使用base_url而不是openai_api_base
            temperature=self.config.get("temperature"),
            max_tokens=self.config.get("max_token"),
            streaming=False
        )


    def set_graph_with_tools(self, tech_tools):
        """
        使用动态提供的 tech_tools 重新设置 graph。

        Args:
            tech_tools: 从外部传入的 MCP tools 列表
        """
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            tech_tools=tech_tools,  # 直接传入 tools
        )
        self.graph = self.graph_setup.set_graph()
        return self.graph
        # try:
        #     # display(Image(graph.get_graph().draw_mermaid_png()))
        #     with open("./graph_main.png", "wb") as f:
        #         png_data = self.graph.get_graph().draw_mermaid_png()
        #         f.write(png_data)  # 手动查看文件
        # except Exception as e:
        #     print(e)

    
    def refresh_llms(self):
        """
        Refresh the LLM objects with the current API key from environment.
        This is called when the API key is updated.
        """
        # Recreate LLM objects with current environment API key and config values
        self.agent_llm = ChatOpenAI(
            model=self.config.get("agent_llm_model", "gpt-4o-mini"),
            temperature=self.config.get("agent_llm_temperature", 0.1)
        )
        self.graph_llm = ChatOpenAI(
            model=self.config.get("graph_llm_model", "gpt-4o"),
            temperature=self.config.get("graph_llm_temperature", 0.1)
        )
        
        # Recreate the graph setup with new LLMs
        self.graph_setup = SetGraph(
            self.agent_llm,
            self.graph_llm,
            trading_graph=self,
        )
        
        # Recreate the main graph
        self.graph = self.graph_setup.set_graph()
