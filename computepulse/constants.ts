import { GpuType, Region, ComputeProvider, TokenProvider, CurrencyConfig, CurrencyCode } from './types';

export const PROVIDERS = ['AWS', 'GCP', 'Azure', 'Lambda', 'Alibaba', 'Tencent', 'Huawei', 'CoreWeave', 'FluidStack', 'Baidu Cloud', 'SenseTime', 'Volcengine'];

// Real-world estimates based on Public List Prices & Spot Markets (approx. USD)
// Hyperscalers are typically 30-50% more expensive than Neo-Clouds
export const TIER_PRICING: Record<string, Record<GpuType, number>> = {
  'HYPERSCALER': { // AWS, GCP, Azure
    [GpuType.H100]: 4.50, // Often bundled in 8-GPU nodes, approx per GPU
    [GpuType.A100]: 3.20,
    [GpuType.V100]: 1.80,
    [GpuType.L40S]: 2.00,
    [GpuType.MLU370]: 0, // N/A
    [GpuType.ASCEND910B]: 0, // N/A
    [GpuType.HYGON_DCU]: 0 // N/A
  },
  'NEOCLOUD': { // Lambda, CoreWeave, FluidStack
    [GpuType.H100]: 2.49, // Aggressive pricing
    [GpuType.A100]: 1.29,
    [GpuType.V100]: 0.55,
    [GpuType.L40S]: 0.90,
    [GpuType.MLU370]: 0, // N/A
    [GpuType.ASCEND910B]: 0, // N/A
    [GpuType.HYGON_DCU]: 0 // N/A
  },
  'CHINA_CLOUD': { // Alibaba, Tencent, Huawei (Supply constrained premiums)
    [GpuType.H100]: 5.50, // Black market / Scarcity premium (Simulated)
    [GpuType.A100]: 3.50,
    [GpuType.V100]: 1.20,
    [GpuType.L40S]: 1.50,
    [GpuType.MLU370]: 1.10, // Domestic chips are cheaper but harder to get in west
    [GpuType.ASCEND910B]: 2.80, // Premium domestic chip
    [GpuType.HYGON_DCU]: 1.00
  }
};

// Regional multipliers reflecting energy costs & supply
export const REGION_MULTIPLIERS: Record<Region, number> = {
  [Region.US_EAST]: 1.0,   // Baseline
  [Region.US_WEST]: 1.05,  // Higher energy
  [Region.EU_CENTRAL]: 1.30, // High energy tax
  [Region.CHINA_EAST]: 1.0, // Baseline for China logic
  [Region.ASIA_PACIFIC]: 1.15,
  [Region.SOUTH_AMERICA]: 1.45 // Infrastructure scarcity
};

// --- MACRO INDEX CONSTANTS ---
export const MACRO_CONSTANTS = {
  // Estimated Total Active AI GPUs in Data Centers globally (Simulated)
  EST_GLOBAL_ACTIVE_GPUS: 4200000, 
  
  // Power specs
  AVG_TDP_WATTS: 600, // Weighted avg between A100 (400W) and H100 (700W)
  GLOBAL_PUE: 1.35, // Power Usage Effectiveness (1.0 is perfect)
  
  // Global Industrial Electricity Rate ($/kWh) - Weighted Average
  GLOBAL_KWH_PRICE: 0.12, 
  
  // Hardware Amortization Baseline ($/hr) 
  // e.g. $25k card / 3 years / 24h * utilization
  HARDWARE_AMORTIZATION_HR: 0.95 
};

export const CURRENCIES: CurrencyConfig[] = [
  { code: 'USD', symbol: '$', rate: 1.0 },
  { code: 'CNY', symbol: '¥', rate: 7.25 },
  { code: 'EUR', symbol: '€', rate: 0.92 },
  { code: 'GBP', symbol: '£', rate: 0.78 },
];

export const getProviderTier = (name: string): string => {
  if (['AWS', 'GCP', 'Azure'].includes(name)) return 'HYPERSCALER';
  if (['Alibaba', 'Tencent', 'Huawei', 'Baidu Cloud', 'SenseTime', 'Volcengine'].includes(name)) return 'CHINA_CLOUD';
  return 'NEOCLOUD';
};

// Helper to generate initial state
export const generateMockData = (): ComputeProvider[] => {
  const data: ComputeProvider[] = [];
  
  PROVIDERS.forEach(provider => {
    Object.values(Region).forEach(region => {
      const tier = getProviderTier(provider);
      
      // Filter logic: China clouds mostly in China/Asia
      if (tier === 'CHINA_CLOUD' && ![Region.CHINA_EAST, Region.ASIA_PACIFIC].includes(region)) return;
      // Filter logic: Western clouds less presence in China
      if (tier !== 'CHINA_CLOUD' && region === Region.CHINA_EAST) return;

      // Determine which GPUs this provider likely has
      let availableGpus: GpuType[] = [];
      if (tier === 'CHINA_CLOUD') {
        // China clouds have mix of restricted NVIDIA (older or stockpile) and Domestic
        availableGpus = [GpuType.ASCEND910B, GpuType.MLU370, GpuType.HYGON_DCU, GpuType.A100, GpuType.V100];
      } else {
        // Western clouds have NVIDIA stack
        availableGpus = [GpuType.H100, GpuType.A100, GpuType.V100, GpuType.L40S];
      }

      // Randomly select a GPU type for this "slot"
      const gpuType = availableGpus[Math.floor(Math.random() * availableGpus.length)];
      
      // Pricing Logic: Base Tier Price * Region Multiplier + Small Variance
      const base = TIER_PRICING[tier][gpuType];
      if (base === 0) return; // Skip invalid combos

      const regional = REGION_MULTIPLIERS[region];
      const variance = (Math.random() * 0.2) - 0.1; // +/- 10% spot fluctuation
      
      let finalPrice = base * regional + variance;

      // Special Case: Scarcity premium for H100 in high demand regions
      if (gpuType === GpuType.H100 && Math.random() > 0.8) {
        finalPrice *= 1.2; // Surge pricing
      }

      data.push({
        id: `${provider}-${region}-${gpuType}`,
        name: provider,
        region: region,
        gpuType: gpuType,
        pricePerHour: parseFloat(finalPrice.toFixed(3)),
        availability: Math.floor(Math.random() * (tier === 'HYPERSCALER' ? 90 : 60)) + 10, // Hyperscalers have better stock
        lastUpdated: new Date().toISOString()
      });
    });
  });
  
  return data;
};

// Expanded list of Global Models (Hugging Face Open Weights + Commercial APIs)
export const generateMockTokenData = (): TokenProvider[] => [
  // --- Proprietary / Closed Source ---
  { id: 'gpt-4o', provider: 'OpenAI', model: 'GPT-4o', inputCost: 2.50, outputCost: 10.00, benchmark: 88.7, latency: 450, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'gpt-4o-mini', provider: 'OpenAI', model: 'GPT-4o Mini', inputCost: 0.15, outputCost: 0.60, benchmark: 82.0, latency: 150, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'claude-3-5-sonnet', provider: 'Anthropic', model: 'Claude 3.5 Sonnet', inputCost: 3.00, outputCost: 15.00, benchmark: 88.3, latency: 500, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'claude-3-haiku', provider: 'Anthropic', model: 'Claude 3 Haiku', inputCost: 0.25, outputCost: 1.25, benchmark: 75.2, latency: 180, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'gemini-1.5-pro', provider: 'Google', model: 'Gemini 1.5 Pro', inputCost: 3.50, outputCost: 10.50, benchmark: 87.8, latency: 380, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'gemini-1.5-flash', provider: 'Google', model: 'Gemini 1.5 Flash', inputCost: 0.075, outputCost: 0.30, benchmark: 78.9, latency: 150, isOpenSource: false, lastUpdated: new Date().toISOString() },
  
  // --- Open Weights (Hugging Face Ecosystem) - US/Europe ---
  { id: 'llama-3-1-405b', provider: 'Meta (Together)', model: 'Llama 3.1 405B', inputCost: 2.50, outputCost: 2.50, benchmark: 87.3, latency: 600, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'llama-3-1-70b', provider: 'Meta (Groq)', model: 'Llama 3.1 70B', inputCost: 0.59, outputCost: 0.79, benchmark: 82.0, latency: 80, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'llama-3-1-8b', provider: 'Meta', model: 'Llama 3.1 8B', inputCost: 0.05, outputCost: 0.05, benchmark: 68.0, latency: 40, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'mistral-large-2', provider: 'Mistral', model: 'Mistral Large 2', inputCost: 2.00, outputCost: 6.00, benchmark: 84.0, latency: 400, isOpenSource: false, lastUpdated: new Date().toISOString() }, // Closed API
  { id: 'mistral-nemo', provider: 'Mistral', model: 'Mistral NeMo 12B', inputCost: 0.15, outputCost: 0.15, benchmark: 74.0, latency: 100, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'gemma-2-27b', provider: 'Google', model: 'Gemma 2 27B', inputCost: 0.27, outputCost: 0.27, benchmark: 76.5, latency: 200, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'phi-3-5-medium', provider: 'Microsoft', model: 'Phi-3.5 Medium', inputCost: 0.10, outputCost: 0.10, benchmark: 73.0, latency: 90, isOpenSource: true, lastUpdated: new Date().toISOString() },
  
  // --- Open Weights (Hugging Face Ecosystem) - China ---
  { id: 'deepseek-v3', provider: 'DeepSeek', model: 'DeepSeek V3', inputCost: 0.14, outputCost: 0.28, benchmark: 88.5, latency: 420, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'deepseek-r1', provider: 'DeepSeek', model: 'DeepSeek R1 (Reasoning)', inputCost: 0.50, outputCost: 2.00, benchmark: 89.1, latency: 800, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'qwen-2-5-72b', provider: 'Alibaba', model: 'Qwen 2.5 72B', inputCost: 0.35, outputCost: 0.40, benchmark: 86.2, latency: 220, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'qwen-2-5-32b', provider: 'Alibaba', model: 'Qwen 2.5 32B', inputCost: 0.15, outputCost: 0.15, benchmark: 78.0, latency: 150, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'yi-large', provider: '01.AI', model: 'Yi Large', inputCost: 2.50, outputCost: 3.00, benchmark: 83.5, latency: 350, isOpenSource: false, lastUpdated: new Date().toISOString() }, // Closed API mostly
  { id: 'glm-4', provider: 'Zhipu AI', model: 'GLM-4', inputCost: 10.00, outputCost: 10.00, benchmark: 85.0, latency: 400, isOpenSource: false, lastUpdated: new Date().toISOString() }, // CNY converted approx
  { id: 'glm-4-9b', provider: 'Zhipu AI', model: 'GLM-4 9B', inputCost: 0.10, outputCost: 0.10, benchmark: 72.0, latency: 80, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'moonshot-v1-8k', provider: 'Moonshot (Kimi)', model: 'Moonshot V1 8k', inputCost: 1.70, outputCost: 1.70, benchmark: 84.5, latency: 300, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'abab-6-5', provider: 'MiniMax', model: 'abab 6.5', inputCost: 2.80, outputCost: 2.80, benchmark: 83.0, latency: 350, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'doubao-pro-32k', provider: 'ByteDance', model: 'Doubao Pro 32k', inputCost: 0.11, outputCost: 0.28, benchmark: 82.5, latency: 120, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'ernie-4-0', provider: 'Baidu', model: 'Ernie 4.0', inputCost: 16.50, outputCost: 16.50, benchmark: 82.0, latency: 500, isOpenSource: false, lastUpdated: new Date().toISOString() },
  { id: 'ernie-3-5', provider: 'Baidu', model: 'Ernie 3.5', inputCost: 1.50, outputCost: 1.50, benchmark: 78.0, latency: 250, isOpenSource: false, lastUpdated: new Date().toISOString() },
  
  // --- Other International ---
  { id: 'command-r-plus', provider: 'Cohere', model: 'Command R+', inputCost: 3.00, outputCost: 15.00, benchmark: 81.0, latency: 450, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'falcon-180b', provider: 'TII', model: 'Falcon 180B', inputCost: 4.00, outputCost: 4.00, benchmark: 79.0, latency: 700, isOpenSource: true, lastUpdated: new Date().toISOString() },
  { id: 'jamba-1-5-large', provider: 'AI21', model: 'Jamba 1.5 Large', inputCost: 2.00, outputCost: 8.00, benchmark: 80.0, latency: 300, isOpenSource: true, lastUpdated: new Date().toISOString() },
];

export const WORLD_MAP_PATHS = {
  // Not used in component currently
};