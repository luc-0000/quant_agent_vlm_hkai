# Quant Agent HK AI

港股量化交易 Agent — LLM 选股 + 技术分析 + **VLM 看图** + 自动交易。

5 个 LLM/VLM 协作：选股、指标分析、形态识别、趋势判断、最终决策，全链路自动化。

## 核心亮点：VLM 看图分析

传统量化只能算指标。这个 Agent 把 K 线画成图表，喂给视觉大模型（VLM），让它像人类交易员一样「看盘」。

**趋势线图 → VLM 直接分析支撑/阻力/突破方向：**

![VLM Trend Analysis](docs/images/vlm-trend-analysis.png)

> VLM 输出：*"Support (blue) is steeply downward-sloping, price has broken below support line decisively — confirmed breakdown. Resistance (red) has held firm with repeated rejections. Lower highs + lower lows = accelerating downside. Prediction: **Downward**."*

同样的方式，K 线图喂给 VLM 识别 16 种经典形态（头肩顶、双底、三角旗、V 形反转等）。

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
- **看图**: mplfinance 生成趋势线图 + K 线图，VLM（qwen3-vl-plus）像人类交易员一样看图分析支撑阻力、识别形态
- **决策**: 综合指标/形态/趋势三份报告，输出交易信号 + 风险收益比 + 预测周期
- **执行**: 自动调 HK AI 接口下单，买入按可用资金和价格算量，卖出按持仓清仓

## 运行

```bash
python main.py              # 自动选股 → 分析 → 交易
python main.py 00388.HK     # 指定股票
```

### 环境变量

| 变量 | 说明 |
|------|------|
| `HKAI_MCP_TOKEN` | HK AI 比赛 Token |
| `DASHSCOPE_API_KEY` | DashScope API Key |
