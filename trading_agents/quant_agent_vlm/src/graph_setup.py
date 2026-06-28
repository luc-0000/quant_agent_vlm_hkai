from langgraph.graph import END, StateGraph, START
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import ToolNode
from trading_agents.quant_agent_vlm.src.agent_state import IndicatorAgentState
from trading_agents.quant_agent_vlm.src.decision_agent import create_final_trade_decider
from trading_agents.quant_agent_vlm.src.indicator_agent import create_indicator_agent
from trading_agents.quant_agent_vlm.src.pattern_agent import create_pattern_agent
from trading_agents.quant_agent_vlm.src.trend_agent import create_trend_agent


class SetGraph:
    def __init__(
        self,
        agent_llm: ChatOpenAI,
        graph_llm: ChatOpenAI,
        tech_tools: list = None,
    ):
        self.agent_llm = agent_llm
        self.graph_llm = graph_llm
        self.tech_tools = tech_tools
    
    def set_graph(self):
        if self.tech_tools is None:
            raise Exception('Tech tool is empty!')


        # 从 tech_tools 中按名称筛选需要的工具
        def get_tools_by_names(tool_list, names):
            return [tool for tool in tool_list if tool.name in names]

        # Create analyst nodes
        agent_nodes = {}
        tool_nodes = {}
        all_agents = ['indicator', 'pattern', 'trend']

        # create nodes for indicator agent
        indicator_tool_names = ["compute_macd", "compute_rsi", "compute_roc", "compute_stoch", "compute_willr"]
        indicator_tools = get_tools_by_names(self.tech_tools, indicator_tool_names)
        agent_nodes['indicator'] = create_indicator_agent(self.agent_llm, indicator_tools)
        tool_nodes['indicator'] = ToolNode(indicator_tools)

        # create nodes for pattern agent
        pattern_tool_names = ["generate_kline_image"]
        pattern_tools = get_tools_by_names(self.tech_tools, pattern_tool_names)
        agent_nodes['pattern'] = create_pattern_agent(self.agent_llm, self.graph_llm, pattern_tools)
        tool_nodes['pattern'] = ToolNode(pattern_tools)

        # create nodes for trend agent
        trend_tool_names = ["generate_trend_image"]
        trend_tools = get_tools_by_names(self.tech_tools, trend_tool_names)
        agent_nodes['trend'] = create_trend_agent(self.agent_llm, self.graph_llm, trend_tools)
        tool_nodes['trend'] = ToolNode(trend_tools)

        # create nodes for decision agent
        decision_agent_node = create_final_trade_decider(self.agent_llm)


        # create graph
        graph = StateGraph(IndicatorAgentState)

        # add agent nodes and associated tool nodes to graph
        for agent_type, cur_node in agent_nodes.items():
            graph.add_node(f"{agent_type.capitalize()} Agent", cur_node)
            graph.add_node(f"{agent_type}_tools", tool_nodes[agent_type])

        # add rest of the nodes
        graph.add_node("Decision Maker", decision_agent_node)

        # set start of graph
        graph.add_edge(START, "Indicator Agent")

        # add edges to graph
        for i, agent_type in enumerate(all_agents):
            current_agent = f"{agent_type.capitalize()} Agent"
            current_tools = f"{agent_type}_tools"

            if i == len(all_agents) - 1:
                graph.add_edge(current_agent, "Decision Maker")
            else:
                
                next_agent = f"{all_agents[i + 1].capitalize()} Agent"
                graph.add_edge(current_agent, next_agent)

        
        # Decision Maker Process
        graph.add_edge("Decision Maker", END)

        
        return graph.compile()
