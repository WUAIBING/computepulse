
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
  annualTWh?: number; // Add this prop
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
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      
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
             <span className="text-neon-blue text-3xl font-mono font-bold tracking-tight">
               {currency.symbol}{displayGcci}
             </span>
             <span className="text-gray-500 text-xs font-bold uppercase">/ gpu-{language === 'CN' ? '小时' : 'hr'}</span>
           </div>
        </div>
        
        {/* Composition Bar */}
        <div className="flex w-full h-2 rounded-full overflow-hidden mb-3">
          <div style={{ width: `${pctHardware}%` }} className="bg-purple-500/80 hover:bg-purple-500 transition-colors" title="CapEx (Hardware)"></div>
          <div style={{ width: `${pctEnergy}%` }} className="bg-amber-500/80 hover:bg-amber-500 transition-colors" title="OpEx (Energy)"></div>
          <div style={{ width: `${pctMargin}%` }} className="bg-emerald-500/80 hover:bg-emerald-500 transition-colors" title="Spot Margin"></div>
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-[10px] text-gray-500 font-mono">
           <div className="flex flex-col">
              <span className="text-gray-400 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-purple-500"></div> {t.hwCapex}</span>
              <span className="pl-2.5">{currency.symbol}{displayHardware}/{language === 'CN' ? '小时' : 'hr'}</span>
           </div>
           <div className="flex flex-col">
              <span className="text-gray-400 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-amber-500"></div> {t.energyOpex}</span>
              <span className="pl-2.5">{currency.symbol}{displayEnergy}/{language === 'CN' ? '小时' : 'hr'}</span>
           </div>
           <div className="flex flex-col">
              <span className="text-gray-400 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500"></div> {t.mktPremium}</span>
              <span className="pl-2.5">Variable</span>
           </div>
        </div>
      </div>

      {/* MIDDLE: Token Price Index (GTPI) */}
      <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden hover:border-neon-purple/30 transition-colors`}>
        <div className="flex justify-between items-start mb-3">
           <div className="flex items-center gap-2">
             <h2 className="text-gray-400 text-xs font-bold uppercase tracking-wider">{t.tokenPriceIndex}</h2>
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
             <span className="text-neon-purple text-3xl font-mono font-bold tracking-tight">
               {currency.symbol}{displayTokenPrice}
             </span>
             <span className="text-gray-500 text-xs font-bold uppercase">/ {language === 'CN' ? '百万 Tokens' : '1M tokens'}</span>
           </div>
        </div>
        
        {/* Composition Bar */}
        <div className="flex w-full h-2 rounded-full overflow-hidden mb-3">
          <div style={{ width: `${pctInput}%` }} className="bg-blue-500/80 hover:bg-blue-500 transition-colors" title="Input Cost"></div>
          <div style={{ width: `${pctOutput}%` }} className="bg-pink-500/80 hover:bg-pink-500 transition-colors" title="Output Cost"></div>
        </div>
        
        <div className="grid grid-cols-2 gap-2 text-[10px] text-gray-500 font-mono">
           <div className="flex flex-col">
              <span className="text-gray-400 flex items-center gap-1"><div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div> {t.avgInput}</span>
              <span className="pl-2.5">{currency.symbol}{(inputCost * currency.rate).toFixed(2)}</span>
           </div>
           <div className="flex flex-col text-right">
              <span className="text-gray-400 flex items-center justify-end gap-1">{t.avgOutput} <div className="w-1.5 h-1.5 rounded-full bg-pink-500"></div></span>
              <span className="pr-2.5">{currency.symbol}{(outputCost * currency.rate).toFixed(2)}</span>
           </div>
        </div>

        {/* Background Animation */}
        <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-neon-purple/5 rounded-full blur-3xl pointer-events-none"></div>
      </div>

      {/* RIGHT: GAGL (Physical Index) */}
      <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden group hover:border-amber-500/30 transition-colors`}>
        <div className="flex justify-between items-start mb-3">
           <div className="flex items-center gap-2">
             <h2 className="text-gray-400 text-xs font-bold uppercase tracking-wider">{t.gaglTitle}</h2>
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
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>{t.estActiveGpus}:</span> <span>{(activeGpus / 1000000).toFixed(1)}M Units</span></div>
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>Avg TDP:</span> <span>{MACRO_CONSTANTS.AVG_TDP_WATTS}W</span></div>
                        <div className="flex justify-between"><span className={themeClasses.textMuted}>Global PUE:</span> <span>{MACRO_CONSTANTS.GLOBAL_PUE}</span></div>
                      </div>
                   </div>
             </div>
           </div>
           <div className="flex items-baseline gap-1">
             <span className="text-orange-500 text-3xl font-mono font-bold tracking-tight">
               {calculatedGW.toFixed(3)}
             </span>
             <span className="text-gray-500 text-xs font-bold uppercase">{language === 'CN' ? '吉瓦' : 'GW'}</span>
           </div>
        </div>
        
        {/* Removed chart as requested */}
        {/* <div className="h-24 w-full mb-4">
          <TokenTrendChart 
             data={tokenHistory.map(p => ({ ...p, price: calculatedGW + (Math.random() * 0.02 - 0.01) }))} // Mock small fluctuation around base
             lineColor="#f97316" 
             fillColor="#f97316" 
             height="100%" 
             showXAxis={false}
             showYAxis={false}
          />
        </div> */}
        
        {/* Spacer to match height with other cards */}
        <div className="h-24 w-full mb-4 flex items-center justify-center">
            <div className="text-center">
               <div className="text-4xl font-bold text-amber-500/20 animate-pulse">{calculatedGW.toFixed(1)} GW</div>
               <div className="text-xs text-amber-500/40 mt-1">{language === 'CN' ? '实时负荷' : 'Real-time Load'}</div>
            </div>
        </div>
        
        <div className="grid grid-cols-2 gap-4 text-[10px] text-gray-500 font-mono">
           <div>
             <span className="block text-gray-400">{t.annualizedForecast}</span>
             <div className="flex items-baseline gap-2">
                <span className="text-white font-bold text-xs">{annualizedTWh.toFixed(1)} {language === 'CN' ? '太瓦时' : 'TWh'}</span>
                <span className="text-neon-green font-bold text-xs">
                  {language === 'CN' 
                    ? `${currency.symbol}${((annualizedTWh * 1_000_000_000 * effectiveKwhPrice) / 1_000_000_000 * 10 * currency.rate).toFixed(1)}亿`
                    : `${currency.symbol}${((annualizedTWh * 1_000_000_000 * effectiveKwhPrice) / 1_000_000_000 * currency.rate).toFixed(1)}B`
                  }
                </span>
             </div>
           </div>
           <div className="text-right">
             <span className="block text-gray-400">{t.capacityEquiv}</span>
             <span className="text-amber-500 font-bold">~{Math.round(calculatedGW)} {t.nuclearReactors}</span>
           </div>
        </div>

        {/* Background Animation for Energy */}
        <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-amber-500/5 rounded-full blur-3xl pointer-events-none"></div>

      </div>

    </div>
  );
};
