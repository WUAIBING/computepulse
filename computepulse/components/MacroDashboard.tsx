
import React from 'react';
import { CurrencyConfig, Language, HistoricalDataPoint, Theme } from '../types';
import { MACRO_CONSTANTS } from '../constants';
import { TRANSLATIONS } from '../translations';
import { TokenTrendChart } from './TokenTrendChart';
import { getThemeClasses } from '../theme';

interface MacroDashboardProps {
  avgSpotPrice: number; // Base USD
  activeGpus: number;
  tokenHistory?: HistoricalDataPoint[];
  kwhPrice?: number;
  annualTWh?: number; 
  industryIndex?: { score: number; trend: string; summary: string } | null;
  currency: CurrencyConfig;
  language: Language;
  theme: Theme;
}

export const MacroDashboard: React.FC<MacroDashboardProps> = ({ 
  avgSpotPrice, 
  activeGpus, 
  tokenHistory = [],
  kwhPrice,
  annualTWh,
  industryIndex,
  currency,
  language,
  theme
}) => {
  const {
    // showCostInfo, setShowCostInfo, // Removed state-based tooltip
    // showTokenInfo, setShowTokenInfo, // Removed state-based tooltip
    // showPowerInfo, setShowPowerInfo // Removed state-based tooltip
  } = React.useMemo(() => ({}), []); // Placeholder to avoid breaking destructuring if any
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);

  const effectiveKwhPrice = kwhPrice !== undefined ? kwhPrice : MACRO_CONSTANTS.GLOBAL_KWH_PRICE;

  // --- CALCULATION LOGIC ---
  const kWhPerHour = (MACRO_CONSTANTS.AVG_TDP_WATTS / 1000) * MACRO_CONSTANTS.GLOBAL_PUE;
  const energyCostPerHr = kWhPerHour * effectiveKwhPrice;
  const hardwareCostPerHr = MACRO_CONSTANTS.HARDWARE_AMORTIZATION_HR;
  const gcciValue = avgSpotPrice; 
  
  const marginEstimate = Math.max(0, avgSpotPrice - energyCostPerHr - hardwareCostPerHr);
  const totalBase = energyCostPerHr + hardwareCostPerHr + marginEstimate;
  
  const pctEnergy = (energyCostPerHr / totalBase) * 100;
  const pctHardware = (hardwareCostPerHr / totalBase) * 100;
  const pctMargin = (marginEstimate / totalBase) * 100;

  // If annualTWh is available (e.g., 340 TWh), we reverse calculate the GW for display consistency
  // Formula: GW = TWh / 8.76
  const calculatedGW = annualTWh ? (annualTWh / 8.76) : (activeGpus * MACRO_CONSTANTS.AVG_TDP_WATTS * MACRO_CONSTANTS.GLOBAL_PUE / 1_000_000_000);
  
  // Use fetched TWh if available, otherwise calculate
  const annualizedTWh = annualTWh || (calculatedGW * 8.76);

  // Formatting
  const displayGcci = (gcciValue * currency.rate).toFixed(2);
  const displayEnergy = (energyCostPerHr * currency.rate).toFixed(2);
  const displayHardware = (hardwareCostPerHr * currency.rate).toFixed(2);

  // Token Metrics (GTPI)
  const latestTokenPrice = tokenHistory.length > 0 ? tokenHistory[tokenHistory.length - 1].price : 2.5; // Default fallback
  const displayTokenPrice = (latestTokenPrice * currency.rate).toFixed(2);

  // Mock breakdown for Token Index
  const inputCost = latestTokenPrice * 0.3;
  const outputCost = latestTokenPrice * 0.7;
  const pctInput = 30;
  const pctOutput = 70;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
      
      {/* LEFT: GCCI (Financial Index) */}
      <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden group hover:border-neon-blue/30 transition-colors`}>
        <div className="flex justify-between items-start mb-3">
           <div className="flex items-center gap-2">
             <h2 className={`${themeClasses.textMuted} text-xs font-bold uppercase tracking-wider`}>{t.gcciTitle}</h2>
             <div 
                className="relative overflow-visible group"
              >
                <svg className="w-4 h-4 text-gray-500 cursor-help hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                
                   <div className={`absolute left-1/2 -translate-x-1/2 md:left-0 md:translate-x-0 bottom-full mb-2 w-72 max-w-[calc(100vw-2rem)] ${theme === 'dark' ? 'bg-black/95 border-gray-700' : 'bg-white border-gray-300 shadow-xl'} border p-4 rounded-lg shadow-2xl z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                      <div className="text-neon-blue font-bold text-sm mb-2">{t.gcciMethodology}</div>
                      <p className={`text-xs ${themeClasses.textMuted} mb-3 leading-relaxed`}>
                        {t.gcciDesc}
                      </p>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>{t.globalEnergyRate}:</span> <span>${effectiveKwhPrice.toFixed(3)}/kWh</span></div>
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>{t.hardwareAmort}:</span> <span>${MACRO_CONSTANTS.HARDWARE_AMORTIZATION_HR}/{language === 'CN' ? '小时' : 'hr'}</span></div>
                      </div>
                   </div>
             </div>
           </div>
           <div className="flex items-baseline gap-1">
             <span className="text-neon-blue text-2xl md:text-3xl font-mono font-bold tracking-tight">
               {currency.symbol}{displayGcci}
             </span>
             <span className={`text-[10px] md:text-xs font-bold uppercase ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>/ gpu-{language === 'CN' ? '小时' : 'hr'}</span>
           </div>
        </div>
        
        {/* Composition Bar */}
        <div className="flex w-full h-2 rounded-full overflow-hidden mb-3">
          <div style={{ width: `${pctHardware}%` }} className="bg-purple-500/80 hover:bg-purple-500 transition-colors" title="CapEx (Hardware)"></div>
          <div style={{ width: `${pctEnergy}%` }} className="bg-amber-500/80 hover:bg-amber-500 transition-colors" title="OpEx (Energy)"></div>
          <div style={{ width: `${pctMargin}%` }} className="bg-emerald-500/80 hover:bg-emerald-500 transition-colors" title="Spot Margin"></div>
        </div>
        
        <div className="grid grid-cols-3 gap-1 text-[10px] font-mono">
           <div className="flex flex-col">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'} flex items-center gap-1 whitespace-nowrap`}><div className="w-1.5 h-1.5 rounded-full bg-purple-500 shrink-0"></div> {t.hwCapex}</span>
              <span className={`pl-2.5 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>{currency.symbol}{displayHardware}/{language === 'CN' ? '小时' : 'hr'}</span>
           </div>
           <div className="flex flex-col">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'} flex items-center gap-1 whitespace-nowrap`}><div className="w-1.5 h-1.5 rounded-full bg-amber-500 shrink-0"></div> {t.energyOpex}</span>
              <span className={`pl-2.5 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>{currency.symbol}{displayEnergy}/{language === 'CN' ? '小时' : 'hr'}</span>
           </div>
           <div className="flex flex-col">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'} flex items-center gap-1 whitespace-nowrap`}><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0"></div> {t.mktPremium}</span>
              <span className={`pl-2.5 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>Variable</span>
           </div>
        </div>
      </div>

      {/* MIDDLE: Token Price Index (GTPI) */}
      <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden hover:border-neon-purple/30 transition-colors`}>
        <div className="flex justify-between items-start mb-3">
           <div className="flex items-center gap-2">
             <h2 className={`${themeClasses.textMuted} text-xs font-bold uppercase tracking-wider`}>{t.tokenPriceIndex}</h2>
             <div 
                className="relative overflow-visible group"
              >
                <svg className="w-4 h-4 text-gray-500 cursor-help hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                
                  <div className={`absolute left-1/2 -translate-x-1/2 md:left-0 md:translate-x-0 bottom-full mb-2 w-72 max-w-[calc(100vw-2rem)] ${theme === 'dark' ? 'bg-black/95 border-gray-700' : 'bg-white border-gray-300 shadow-xl'} border p-4 rounded-lg shadow-2xl z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                    <div className="text-neon-purple font-bold text-sm mb-2">{t.tokenMethodology}</div>
                    <p className={`text-xs ${themeClasses.textMuted} mb-3 leading-relaxed`}>
                      {t.tokenDesc}
                    </p>
                  </div>
             </div>
           </div>
           <div className="flex items-baseline gap-1">
             <span className="text-neon-purple text-2xl md:text-3xl font-mono font-bold tracking-tight">
               {currency.symbol}{displayTokenPrice}
             </span>
             <span className={`text-[10px] md:text-xs font-bold uppercase ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>/ {language === 'CN' ? '百万 Tokens' : '1M tokens'}</span>
           </div>
        </div>
        
        {/* Composition Bar */}
        <div className="flex w-full h-2 rounded-full overflow-hidden mb-3">
          <div style={{ width: `${pctInput}%` }} className="bg-blue-500/80 hover:bg-blue-500 transition-colors" title="Input Cost"></div>
          <div style={{ width: `${pctOutput}%` }} className="bg-pink-500/80 hover:bg-pink-500 transition-colors" title="Output Cost"></div>
        </div>
        
        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
           <div className="flex flex-col">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'} flex items-center gap-1 whitespace-nowrap`}><div className="w-1.5 h-1.5 rounded-full bg-blue-500 shrink-0"></div> {t.avgInput}</span>
              <span className={`pl-2.5 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>{currency.symbol}{(inputCost * currency.rate).toFixed(2)}</span>
           </div>
           <div className="flex flex-col text-right">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'} flex items-center justify-end gap-1 whitespace-nowrap`}>{t.avgOutput} <div className="w-1.5 h-1.5 rounded-full bg-pink-500 shrink-0"></div></span>
              <span className={`pr-2.5 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>{currency.symbol}{(outputCost * currency.rate).toFixed(2)}</span>
           </div>
        </div>

        {/* Background Animation */}
        <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-neon-purple/5 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* RIGHT: GAGL (Physical Index) */}
      <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden group hover:border-amber-500/30 transition-colors`}>
        <div className="flex justify-between items-start mb-3">
           <div className="flex items-center gap-2">
             <h2 className={`${themeClasses.textMuted} text-xs font-bold uppercase tracking-wider`}>{t.gaglTitle}</h2>
             <div 
                className="relative overflow-visible group"
              >
                <svg className="w-4 h-4 text-gray-500 cursor-help hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                
                   <div className={`absolute left-1/2 -translate-x-1/2 md:left-0 md:translate-x-0 bottom-full mb-2 w-72 max-w-[calc(100vw-2rem)] ${theme === 'dark' ? 'bg-black/95 border-gray-700' : 'bg-white border-gray-300 shadow-xl'} border p-4 rounded-lg shadow-2xl z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                      <div className="text-amber-500 font-bold text-sm mb-2">{t.energyModel}</div>
                      <p className={`text-xs ${themeClasses.textMuted} mb-3 leading-relaxed`}>
                        {t.energyDesc}
                      </p>
                      <div className={`font-mono ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-300'} p-2 rounded border text-xs mb-2`}>
                         Load = GPUs × TDP × PUE
                      </div>
                      <div className="space-y-1 text-xs">
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>{t.activeGPUs}:</span> <span>{activeGpus.toLocaleString()}</span></div>
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>{t.avgTDP}:</span> <span>{MACRO_CONSTANTS.AVG_TDP_WATTS}W</span></div>
                      </div>
                   </div>
             </div>
           </div>
           <div className="flex items-baseline gap-1">
             <span className="text-amber-500 text-2xl md:text-3xl font-mono font-bold tracking-tight">
               {annualizedTWh.toFixed(3)}
             </span>
             <span className={`text-[10px] md:text-xs font-bold uppercase ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
               {annualTWh ? 'TWh' : 'GW'}
             </span>
           </div>
        </div>
        
        {/* Composition Bar */}
        <div className="flex w-full h-2 rounded-full overflow-hidden mb-3 bg-gray-700/30">
          <div className="w-full h-full bg-amber-500/80 hover:bg-amber-500 transition-colors relative overflow-hidden">
             <div className="absolute inset-0 w-full h-full bg-[linear-gradient(90deg,transparent,rgba(255,255,255,0.2),transparent)] animate-[shimmer_2s_infinite]"></div>
          </div>
        </div>
        
        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
           <div className="flex flex-col">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'} flex items-center gap-1 whitespace-nowrap`}>{t.dataSource}</span>
              <span className={`pl-0 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>{t.publicListPrice}</span>
           </div>
           <div className="flex flex-col text-right">
              <span className={`${theme === 'dark' ? 'text-emerald-400' : 'text-emerald-600 font-bold'} flex items-center justify-end gap-1 whitespace-nowrap`}><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse shrink-0"></div> {t.systemOperational}</span>
              <span className={`pr-0 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-800'}`}>~{(calculatedGW * 15).toFixed(1)} Nuclear Reactors</span>
           </div>
        </div>

        {/* Background Animation */}
        <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-amber-500/5 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* NEW: AI Industry Prosperity Index (AIPI) */}
      <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden group hover:border-cyan-500/30 transition-colors`}>
        <div className="flex justify-between items-start mb-3">
           <div className="flex items-center gap-2">
             <h2 className={`${themeClasses.textMuted} text-xs font-bold uppercase tracking-wider`}>AIPI Index</h2>
             <div className="relative overflow-visible group">
                <svg className="w-4 h-4 text-gray-500 cursor-help hover:text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                   <div className={`absolute right-0 bottom-full mb-2 w-64 ${theme === 'dark' ? 'bg-black/95 border-gray-700' : 'bg-white border-gray-300 shadow-xl'} border p-4 rounded-lg shadow-2xl z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                      <div className="text-cyan-500 font-bold text-sm mb-2">AI Industry Prosperity Index</div>
                      <p className={`text-xs ${themeClasses.textMuted} mb-2 leading-relaxed`}>
                        {language === 'CN' ? '综合 GPU 租赁价格、巨头 Capex 支出与模型发布频率的实时指数。' : 'Real-time index synthesizing GPU rental prices, Giant Capex spend, and model release frequency.'}
                      </p>
                      <div className="text-[10px] text-gray-500">Source: GLM Analysis</div>
                   </div>
             </div>
           </div>
           <div className="flex items-baseline gap-1">
             <span className={`text-2xl md:text-3xl font-mono font-bold tracking-tight ${industryIndex ? (industryIndex.score > 60 ? 'text-cyan-500' : industryIndex.score < 40 ? 'text-red-500' : 'text-yellow-500') : 'text-gray-600'}`}>
               {industryIndex ? industryIndex.score : '--'}
             </span>
             <span className={`text-[10px] md:text-xs font-bold uppercase ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
               / 100
             </span>
           </div>
        </div>
        
        {/* Sentiment Bar */}
        <div className="flex w-full h-2 rounded-full overflow-hidden mb-3 bg-gray-700/30">
          <div style={{ width: industryIndex ? `${industryIndex.score}%` : '0%' }} className={`h-full transition-all duration-1000 ${industryIndex && industryIndex.score > 60 ? 'bg-cyan-500' : 'bg-yellow-500'}`}></div>
        </div>
        
        <div className="flex flex-col gap-1 text-[10px] font-mono min-h-[40px]">
           <div className="flex justify-between items-center">
              <span className={`${theme === 'dark' ? 'text-gray-400' : 'text-gray-600 font-medium'}`}>Trend</span>
              <span className={`${industryIndex?.trend === 'up' ? 'text-emerald-400' : industryIndex?.trend === 'down' ? 'text-red-400' : 'text-gray-400'} uppercase font-bold flex items-center gap-1`}>
                {industryIndex?.trend === 'up' ? '▲ BULLISH' : industryIndex?.trend === 'down' ? '▼ BEARISH' : '▶ NEUTRAL'}
              </span>
           </div>
           <div className={`leading-tight mt-1 truncate ${theme === 'dark' ? 'text-gray-500' : 'text-gray-700'}`} title={industryIndex?.summary}>
              {industryIndex ? industryIndex.summary : (language === 'CN' ? '正在分析资本支出数据...' : 'Analyzing Capex data...')}
           </div>
        </div>

        {/* Background Animation */}
        <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none"></div>
      </div>

    </div>
  );
};
