
export enum GpuType {
  H100 = 'NVIDIA H100',
  A100 = 'NVIDIA A100',
  V100 = 'NVIDIA V100',
  L40S = 'NVIDIA L40S',
  MLU370 = 'Cambricon MLU370', // 寒武纪
  ASCEND910B = 'Huawei Ascend 910B', // 华为昇腾
  HYGON_DCU = 'Hygon DCU' // 海光
}

export enum Region {
  US_EAST = 'US-East',
  US_WEST = 'US-West',
  EU_CENTRAL = 'EU-Central',
  CHINA_EAST = 'China-East',
  ASIA_PACIFIC = 'Asia-Pacific',
  SOUTH_AMERICA = 'South America'
}

export interface ComputeProvider {
  id: string;
  name: string;
  region: Region;
  pricePerHour: number;
  availability: number; // 0-100%
  gpuType: GpuType;
  lastUpdated: string;
}

export interface TokenProvider {
  id: string;
  provider: string;
  model: string;
  inputCost: number; // $ per 1M tokens
  outputCost: number; // $ per 1M tokens
  benchmark: number; // MMLU Score (0-100)
  latency: number; // ms (mock)
  isOpenSource: boolean; // True for HuggingFace/Open Weights
  lastUpdated: string;
}

export interface MarketInsight {
  summary: string;
  trend: 'UP' | 'DOWN' | 'STABLE';
  reasoning: string;
}

export interface HistoricalDataPoint {
  time: string;
  price: number;
}

export type CurrencyCode = 'USD' | 'CNY' | 'EUR' | 'GBP' | 'JPY';
export type Language = 'EN' | 'CN';

export interface CurrencyConfig {
  code: CurrencyCode;
  symbol: string;
  rate: number; // Exchange rate relative to USD
}
