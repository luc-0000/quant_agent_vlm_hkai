# Quant Agent HK AI

港股量化交易 Agent — LLM 选股 + 技术分析 + VLM 看图 + 自动交易。

5 个 LLM/VLM 协作：选股、指标分析、形态识别、趋势判断、最终决策，全链路自动化。

## 5-Agent 协作流程

```
LLM 选股                           qwen-plus
  │  全量扫描142只港股，挑最有潜力的1只
  ▼
技术指标分析                        qwen-plus
  │  TA-Lib 计算 RSI / MACD / Stoch / ROC / 威廉%R
  │  LLM 解读指标，判断超买超卖、背离、交叉信号
  ▼
┌──────────────┬──────────────┐
│ 形态识别      │ 趋势分析      │   qwen3-vl-plus (VLM) × 2
│ K线 → 图表    │ 趋势线 → 图表  │
│ VLM 看图识别  │ VLM 分析支撑   │
│ 16种经典形态  │ 阻力/突破方向  │
└──────────────┴──────────────┘
  ▼
最终决策                           qwen-plus
  │  综合三份报告 → LONG / SHORT / HOLD
  │  含风险收益比 + 预测周期 + 决策理由
  ▼
交易执行
  │  LONG → buy_stock()  /  SHORT → sell_stock()
```

- **选股**: 调 `list_selectable_stocks` + `get_quote_by_symbols` 获取全量行情，LLM 根据动量、流动性、波动率挑选
- **指标**: 本地 TA-Lib 计算 5 个技术指标，LLM 解读写报告
- **看图**: mplfinance 生成 K 线图 + 趋势线图，VLM 识别形态、判断趋势
- **决策**: 综合指标/形态/趋势三份报告，输出交易信号
- **执行**: 自动调 HK AI 接口下单，买按资金/价格算量，卖按持仓清仓

## 项目结构

```
├── main.py                       # 入口：选股 → 分析 → 交易
├── Dockerfile                    # python:3.12-slim
├── requirements.txt              # 全部依赖
├── skills/hk_ai/                 # HK AI 行情/交易 API (17个工具)
├── trading_agents/
│   ├── common/utils.py           # Action / PositionSignal 枚举
│   └── quant_agent_vlm/
│       ├── main.py               # qa_main() 分析入口
│       ├── default_config.py     # LLM 模型配置 (DashScope)
│       └── src/
│           ├── stock_selector.py # LLM 选股
│           ├── analyzer.py       # 数据获取 + 分析编排
│           ├── trading_graph.py  # LLM 初始化 + 图编译
│           ├── graph_setup.py    # StateGraph 节点连接
│           ├── indicator_agent.py
│           ├── pattern_agent.py  # VLM 形态识别
│           ├── trend_agent.py    # VLM 趋势分析
│           ├── decision_agent.py # 最终决策
│           └── color_style.py    # K线图配色
├── mcp_servers/tech_mcp_servers/
│   ├── tech_tools_mcp.py         # 7个MCP工具 (RSI/MACD/图表等)
│   └── tech_tools_mcp_utils.py   # 趋势线拟合
└── docs/FLOW.md                  # 详细流程文档
```

## 运行

```bash
# 自动选股 + 分析 + 交易
python main.py

# 指定股票
python main.py 00388.HK
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `HKAI_MCP_TOKEN` | HK AI 比赛 Token |
| `DASHSCOPE_API_KEY` | DashScope API Key |

## 数据源

| 数据 | 来源 |
|------|------|
| 股票列表/行情 | HK AI MCP |
| K 线 | HK AI MCP `get_stock_kline` |
| 技术指标 | 本地 TA-Lib |
| K 线图表 | 本地 mplfinance |
