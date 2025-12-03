
import React, { useState } from 'react';
import { CurrencyConfig, Language } from '../types';
import { TRANSLATIONS } from '../translations';

interface MarketVitalsProps {
  cvix: number; // Compute Volatility Index
  currency: CurrencyConfig;
  language: Language;
  kwhPrice?: number;
}

export const MarketVitals: React.FC<MarketVitalsProps> = ({ cvix, currency, language, kwhPrice }) => {
  const [showCvixInfo, setShowCvixInfo] = useState(false);
  const t = TRANSLATIONS[language];

  // Determine color based on CVIX
  const cvixColor = cvix > 30 ? 'text-red-500' : cvix > 15 ? 'text-amber-500' : 'text-emerald-500';
  const cvixLabel = cvix > 30 ? t.highVol : cvix > 15 ? t.moderate : t.stable;
  
  // Use the real fetched price if available, otherwise fallback to 0.12 USD
  const effectivePrice = kwhPrice !== undefined ? kwhPrice : 0.12;
  const energyPrice = (effectivePrice * currency.rate).toFixed(3);

  return (
    <div className="bg-panel-bg rounded-xl border border-gray-800 p-6 space-y-6 overflow-visible">
      
      {/* Header */}
      <h3 className="text-lg font-bold text-white border-b border-gray-800 pb-2">
        {t.marketVitals}
      </h3>

      {/* CVIX Widget */}
      <div>
        <div className="flex justify-between items-end mb-2 relative">
          <span className="text-gray-400 text-sm font-mono flex items-center gap-2">
            {t.cvixIndex}
            <div 
              className="relative group"
              onMouseEnter={() => setShowCvixInfo(true)}
              onMouseLeave={() => setShowCvixInfo(false)}
            >
              <svg className="w-4 h-4 text-gray-500 cursor-help hover:text-neon-blue transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              {/* Tooltip Popup */}
              <div className={`absolute left-0 top-6 w-64 bg-black/95 border border-gray-700 p-3 rounded-lg shadow-2xl text-xs text-gray-300 transition-opacity duration-200 z-50 pointer-events-none ${showCvixInfo ? 'opacity-100' : 'opacity-0'}`}>
                <div className="font-bold text-neon-blue mb-1">{t.cvixIndex}</div>
                <div className="mb-2">{t.cvixDesc}</div>
                <div className="font-mono bg-gray-900 p-1 rounded border border-gray-800 text-center mb-2">
                  CVIX = (StdDev / Mean) × 100
                </div>
              </div>
            </div>
          </span>
          <span className={`text-2xl font-bold font-mono ${cvixColor}`}>
            {cvix.toFixed(2)}
          </span>
        </div>
        <div className="w-full bg-gray-800 h-2 rounded-full overflow-hidden mb-1">
          <div 
            className={`h-full transition-all duration-1000 ${cvix > 30 ? 'bg-red-500' : cvix > 15 ? 'bg-amber-500' : 'bg-emerald-500'}`}
            style={{ width: `${Math.min(cvix * 2, 100)}%` }}
          />
        </div>
        <div className="flex justify-between text-[10px] text-gray-500 uppercase tracking-wider">
          <span>{t.fearSpread}</span>
          <span>{cvixLabel}</span>
        </div>
      </div>

      {/* Energy Index Mockup */}
      <div className="pt-4 border-t border-gray-800">
         <div className="flex justify-between items-center">
            <span className="text-xs text-gray-400">{t.estEnergyRate}</span>
            <span className="text-sm text-neon-green font-mono">{currency.symbol}{energyPrice}/kWh</span>
         </div>
      </div>

    </div>
  );
};
