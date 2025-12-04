
import { Language } from './types';

export const TRANSLATIONS = {
  EN: {
    appTitle: "Global Compute Pulse",
    dataSource: "Data Source",
    dataSourceDesc: "Public List Price & Spot Estimation",
    systemOperational: "System Operational",
    
    // Header
    viewGpu: "GPU Compute",
    viewToken: "Token Inference",
    viewGridLoad: "Grid Load",
    unit: "UNIT",

    // Macro Dashboard
    gcciTitle: "GCCI • Global Compute Cost Index",
    gcciMethodology: "Index Methodology",
    gcciDesc: "Composite index tracking the weighted average hourly cost of high-performance compute (H100 eqv). Includes energy OpEx, hardware amortization, and spot market premiums.",
    tokenPriceIndex: "GTPI • Global Token Price Index",
    tokenMethodology: "Weighted Average Pricing",
    tokenDesc: "Real-time average cost for 1M tokens across major providers (OpenAI, Anthropic, DeepSeek, etc.). Weighted by estimated market usage volume.",
    avgInput: "Avg Input",
    avgOutput: "Avg Output",
    blended: "Blended",
    globalEnergyRate: "Global Energy Rate",
    hardwareAmort: "Hardware Amort",
    hwCapex: "HW CapEx",
    energyOpex: "Energy OpEx",
    mktPremium: "Mkt Premium",
    
    gaglTitle: "GAGL • Global AI Grid Load",
    energyModel: "Energy Consumption Model",
    energyDesc: "Real-time estimate of total electricity drawn by global AI data centers.",
    estActiveGpus: "Est. Active GPUs",
    realTime: "Real-time",
    annualizedForecast: "Global Data Center Energy Forecast",
    capacityEquiv: "Capacity Equivalence",
    nuclearReactors: "Nuclear Reactors",

    // Trends & Charts
    gpuIndexTitle: "Global GPU Index (Spot Price)",
    last60s: "Last 60 Seconds",
    globalHeatmap: "Global Cost Heatmap",
    avgHourlyCost: "Avg. Hourly Cost",
    global: "Global",
    instanceMix: "Instance: Global Mix",
    
    // Token Chart
    modelPricingIndex: "Global Model Pricing Index",
    sviIndex: "Smart Value Index (SVI)",
    stdTco: "Standardized TCO",
    stdTcoDesc: "Total Cost of Ownership for 1M full-cycle tokens.",
    calcMethod: "Calculation Method",
    sviDesc: "SVI measures Intelligence Return on Investment.",
    pricePer1M: "Price per 1M Tokens",
    intelligencePer: "Intelligence per",
    costBtn: "Cost",
    valueBtn: "Value",

    // Grid Load Chart
    gridLoadTrend: "Global AI Energy Consumption Trend",
    totalPower: "Total Power Draw",
    gridLoadDesc: "Real-time power consumption of global AI data centers (Gigawatts)",


    // Market Vitals
    marketVitals: "Market Vitals",
    cvixIndex: "CVIX Index",
    cvixDesc: "Measures the \"fear\" or dispersion in global GPU pricing.",
    fearSpread: "Fear & Spread",
    marketDominance: "Market Dominance",
    estEnergyRate: "Est. Global Energy Rate",
    highVol: "HIGH VOLATILITY",
    moderate: "MODERATE",
    stable: "STABLE MARKET",

    // Insight
    // geminiAnalyst: "Qwen Market Analyst",
    // refresh: "Refresh Insight",
    // analyzing: "Analyzing...",
    // marketSummary: "Market Summary",
    // analystReasoning: "Analyst Reasoning",
    // trend: "TREND",
    
    // Stats
    lowestRate: "Lowest Rate Found",
    highDemand: "High Demand Zone",
    limitedAvail: "Limited Availability",
    verifyData: "Verify Data",

    // Calculation Modal
    calcTitle: "Calculation Verification",
    calcDesc: "Transparent breakdown of pricing models and indices",
    gpuPricing: "GPU Compute Pricing",
    tokenSvi: "Token Inference SVI",
    providerRegion: "Provider / Region",
    basePrice: "Base Price",
    regMult: "Reg. Multiplier",
    estVar: "Est. Variance",
    finalPrice: "Final",
    converted: "Converted",
    surge: "SURGE",
    formula: "Formula:",
    formulaDesc: "Final Price = (Base Tier Price × Region Multiplier) + Spot Variance + (Surge Premium if applicable)",
    sviFormula: "SVI Formula (Smart Value Index):",
    sviFormulaDesc: "SVI = Benchmark Score / Total Cost per 1M Tokens",
    higherBetter: "(Higher is Better - More Intelligence per Dollar)",
    exchangeRateApplied: "Exchange Rate Applied:",
    model: "Model",
    input1M: "Input ($/1M)",
    output1M: "Output ($/1M)",
    total1M: "Total ($/1M)",
    totalLocal: "Total",
    benchmark: "Benchmark (MMLU)",
    sviScore: "SVI Score",
  },
  CN: {
    appTitle: "算力脉搏",
    dataSource: "数据来源",
    dataSourceDesc: "公开标价与现货估算",
    systemOperational: "系统运行中",
    
    // Header
    viewGpu: "GPU 算力成本",
    viewToken: "Token 推理成本",
    viewGridLoad: "电网负荷",
    unit: "单位",

    // Macro Dashboard
    gcciTitle: "GCCI • 全球算力成本指数",
    gcciMethodology: "指数编制方法",
    gcciDesc: "追踪高性能计算（H100等效）加权平均小时成本的综合指数。包含能源运营支出(OpEx)、硬件摊销和现货市场溢价。",
    tokenPriceIndex: "GTPI • 全球 Token 价格指数",
    tokenMethodology: "加权平均定价",
    tokenDesc: "主要服务商（OpenAI, Anthropic, DeepSeek等）每百万 Token 的实时平均成本。根据预估市场用量加权。",
    avgInput: "平均输入",
    avgOutput: "平均输出",
    blended: "混合成本",
    globalEnergyRate: "全球能源费率",
    hardwareAmort: "硬件摊销",
    hwCapex: "硬件资本支出",
    energyOpex: "能源运营支出",
    mktPremium: "市场溢价",
    
    gaglTitle: "GAGL • 全球 AI 电网负荷",
    energyModel: "能耗模型",
    energyDesc: "全球 AI 数据中心总耗电量的实时估算值。",
    estActiveGpus: "预估活跃 GPU",
    realTime: "实时",
    annualizedForecast: "全球数据中心年化能耗预测",
    capacityEquiv: "容量等效",
    nuclearReactors: "座核反应堆",
    verifyData: "验证数据",

    // Calculation Modal
    calcTitle: "数据计算验证",
    calcDesc: "定价模型与指数的透明化拆解",
    gpuPricing: "GPU 算力定价",
    tokenSvi: "Token 推理 SVI",
    providerRegion: "服务商 / 区域",
    basePrice: "基础价格",
    regMult: "区域系数",
    estVar: "预估波动",
    finalPrice: "最终价格",
    converted: "换算后",
    surge: "溢价",
    formula: "公式:",
    formulaDesc: "最终价格 = (基础层级价格 × 区域系数) + 现货波动 + (溢价，如适用)",
    sviFormula: "SVI 公式 (智能价值指数):",
    sviFormulaDesc: "SVI = 基准得分 / 每百万 Token 总成本",
    higherBetter: "(越高越好 - 单位美元的智能产出)",
    exchangeRateApplied: "应用汇率:",
    model: "模型",
    input1M: "输入 ($/1M)",
    output1M: "输出 ($/1M)",
    total1M: "总计 ($/1M)",
    totalLocal: "总计",
    benchmark: "基准分 (MMLU)",
    sviScore: "SVI 得分",

    // Trends & Charts
    gpuIndexTitle: "全球 GPU 指数 (现货价格)",
    last60s: "过去 60 秒",
    globalHeatmap: "全球成本热力图",
    avgHourlyCost: "平均小时成本",
    global: "全球",
    instanceMix: "实例: 全球混合 (含国产芯片)",
    
    // Token Chart
    modelPricingIndex: "全球模型定价指数",
    sviIndex: "智能价值指数 (SVI)",
    stdTco: "标准化 TCO",
    stdTcoDesc: "100万个全周期 Token 的总拥有成本。",
    calcMethod: "计算方法",
    sviDesc: "SVI 衡量智能产出的投资回报率。",
    pricePer1M: "每百万 Token 价格",
    intelligencePer: "智能产出 / ",
    costBtn: "成本",
    valueBtn: "价值",

    // Grid Load Chart
    gridLoadTrend: "全球 AI 能耗趋势",
    totalPower: "总功率消耗",
    gridLoadDesc: "全球 AI 数据中心实时功耗 (吉瓦)",

    // Market Vitals
    marketVitals: "市场生命体征",
    cvixIndex: "CVIX 波动率指数",
    cvixDesc: "衡量全球 GPU 定价的“恐慌度”或离散程度。",
    fearSpread: "恐慌与价差",
    marketDominance: "市场主导地位",
    estEnergyRate: "预估全球电价",
    highVol: "高波动",
    moderate: "中等",
    stable: "市场平稳",

    // Insight
    // geminiAnalyst: "通义千问市场分析师",
    // refresh: "刷新观点",
    // analyzing: "分析中...",
    // marketSummary: "市场摘要",
    // analystReasoning: "分析师逻辑",
    // trend: "趋势",
    
    // Stats
    lowestRate: "最低费率",
    highDemand: "高需求区域",
    limitedAvail: "资源紧缺"
  }
};
