# Quant Agent HK AI

港股量化交易 Agent — LLM 选股 + 技术分析 + VLM 看图 + 交易决策。

## 流程

```
list_selectable_stocks() + get_quote_by_symbols()
              │
              ▼
       LLM 选股 (qwen-plus)
       "选出最有短线潜力的1只"
              │
              ▼
       get_stock_kline("00700.HK")
       60 根日 K → DataFrame
              │
              ▼
┌─────────────────────────────────────┐
│  TA-Lib 技术指标 (MCP tools)         │
│  RSI / MACD / Stochastic / ROC / WR │
│              │                       │
│              ▼                       │
│  Indicator Agent (LLM 汇总报告)       │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  图表生成 + VLM 看图                  │
│                                     │
│  K线图 ──▶ VLM 识别16种经典形态      │
│  趋势线图 ──▶ VLM 分析支撑/阻力       │
│                                     │
│  模型: qwen3-vl-plus                │
└─────────────────┬───────────────────┘
                  ▼
┌─────────────────────────────────────┐
│  Decision Agent (LLM)               │
│  指标 + 形态 + 趋势 → 综合决策        │
│                                     │
│  LONG / SHORT / HOLD                │
│  + risk_reward_ratio                │
│  + forecast_horizon                 │
│  + justification                    │
└─────────────────────────────────────┘
```

## 项目结构

```
quant_agent_hkai/
├── main.py                          # 入口：LLM 选股 → 量化分析
├── agent_qa.yml                     # Agent 配置 (fintools framework)
├── skills/hk_ai/                    # HK AI 行情/交易 API
│   ├── trading_api.py               #   17 个 MCP 工具封装
│   ├── SKILL.md                     #   LLM agent 使用说明
│   └── references/api_reference.md  #   API 文档
├── trading_agents/
│   ├── common/utils.py              # Action / PositionSignal 枚举
│   └── quant_agent_vlm/
│       ├── main.py                  # qa_main() 分析入口
│       ├── default_config.py        # LLM 模型配置 (DashScope)
│       └── src/
│           ├── stock_selector.py    # LLM 选股
│           ├── analyzer.py          # 数据获取 + 分析编排
│           ├── agent_state.py       # LangGraph 状态定义
│           ├── trading_graph.py     # LLM 初始化 + 图编译
│           ├── graph_setup.py       # StateGraph 节点连接
│           ├── indicator_agent.py   # 指标分析节点
│           ├── pattern_agent.py     # 形态识别节点 (VLM)
│           ├── trend_agent.py       # 趋势分析节点 (VLM)
│           ├── decision_agent.py    # 最终决策节点
│           └── color_style.py       # K线图配色
├── mcp_servers/
│   ├── utils.py                     # MCP client 工厂
│   └── tech_mcp_servers/
│       ├── tech_tools_mcp.py        # 7 个 MCP 工具 (指标+图表)
│       └── tech_tools_mcp_utils.py  # 趋势线拟合
├── common/consts.py                 # Agent 类型常量
├── data_provider/mairui.py          # (备用) Mairui API
└── docs/FLOW.md                     # 详细流程文档
```

## LLM 调用点

| 阶段 | 模型 | 用途 |
|------|------|------|
| 选股 | `qwen-plus-latest` | 从候选列表挑最有潜力的 1 只 |
| 指标汇总 | `qwen-plus-latest` | 解读 RSI/MACD/Stoch/ROC/WillR |
| 形态识别 | `qwen3-vl-plus` (VLM) | 看 K 线图识别 16 种形态 |
| 趋势分析 | `qwen3-vl-plus` (VLM) | 看趋势线图分析支撑/阻力 |
| 最终决策 | `qwen-plus-latest` | 综合报告输出 LONG/SHORT/HOLD |

## 运行

```bash
# 自动选股 + 分析
python main.py

# 指定股票
python main.py 00388.HK

# 仅量化分析 (跳过选股)
python -c "import asyncio; from trading_agents.quant_agent_vlm.main import qa_main; asyncio.run(qa_main('00700.HK'))"
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `HKAI_MCP_TOKEN` | HK AI 比赛 Token (行情/交易 API) |
| `DASHSCOPE_API_KEY` | DashScope API Key (也可以通过 `default_config.py` 配置) |

## 数据源

| 数据 | 来源 |
|------|------|
| 股票列表/行情 | HK AI MCP `list_selectable_stocks` / `get_quote_by_symbols` |
| K 线 | HK AI MCP `get_stock_kline` |
| 技术指标 | 本地 TA-Lib (MCP tools) |
| K 线图表 | 本地 mplfinance (MCP tools) |
