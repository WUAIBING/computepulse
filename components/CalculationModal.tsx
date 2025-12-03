
import React from 'react';
import { ComputeProvider, TokenProvider, CurrencyConfig, Language } from '../types';
import { TIER_PRICING, REGION_MULTIPLIERS, getProviderTier } from '../constants';
import { TRANSLATIONS } from '../translations';

interface CalculationModalProps {
  isOpen: boolean;
  onClose: () => void;
  computeData: ComputeProvider[];
  tokenData: TokenProvider[];
  currency: CurrencyConfig;
  language: Language;
}

export const CalculationModal: React.FC<CalculationModalProps> = ({ isOpen, onClose, computeData, tokenData, currency, language }) => {
  const [activeTab, setActiveTab] = React.useState<'GPU' | 'TOKEN'>('GPU');
  const t = TRANSLATIONS[language];

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#13131f] border border-gray-700 rounded-xl w-full max-w-6xl h-[80vh] flex flex-col shadow-2xl">
        {/* Header */}
        <div className="flex justify-between items-center p-6 border-b border-gray-800">
          <div>
            <h2 className="text-xl font-bold text-white">{t.calcTitle}</h2>
            <p className="text-gray-400 text-sm mt-1">{t.calcDesc}</p>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-800">
          <button 
            onClick={() => setActiveTab('GPU')}
            className={`px-6 py-3 text-sm font-bold transition-colors ${activeTab === 'GPU' ? 'text-neon-blue border-b-2 border-neon-blue bg-white/5' : 'text-gray-400 hover:text-white'}`}
          >
            {t.gpuPricing}
          </button>
          <button 
            onClick={() => setActiveTab('TOKEN')}
            className={`px-6 py-3 text-sm font-bold transition-colors ${activeTab === 'TOKEN' ? 'text-neon-purple border-b-2 border-neon-purple bg-white/5' : 'text-gray-400 hover:text-white'}`}
          >
            {t.tokenSvi}
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {activeTab === 'GPU' ? (
            <div className="space-y-6">
              <div className="bg-blue-900/20 border border-blue-800 rounded-lg p-4 text-sm text-blue-200 mb-4">
                <strong>Formula:</strong> <code>Final Price = (Base Tier Price × Region Multiplier) + Spot Variance + (Surge Premium if applicable)</code>
              </div>
              <table className="w-full text-left text-xs text-gray-300">
                <thead className="text-gray-500 uppercase font-bold bg-gray-900/50 sticky top-0">
                  <tr>
                    <th className="p-3">{t.providerRegion}</th>
                    <th className="p-3">{t.viewGpu}</th>
                    <th className="p-3 text-right">{t.basePrice} (USD)</th>
                    <th className="p-3 text-right">{t.regMult}</th>
                    <th className="p-3 text-right">{t.estVar}</th>
                    <th className="p-3 text-right">{t.finalPrice} (USD)</th>
                    <th className="p-3 text-right">{t.converted} ({currency.code})</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {computeData.slice(0, 20).map((item, idx) => {
                    const tier = getProviderTier(item.name);
                    const base = TIER_PRICING[tier]?.[item.gpuType] || 0;
                    const multiplier = REGION_MULTIPLIERS[item.region] || 1;
                    
                    const expectedBase = base * multiplier;
                    const diff = item.pricePerHour - expectedBase;
                    const isSurge = diff > (expectedBase * 0.15); 
                    
                    return (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="p-3 font-medium text-white">
                          <div>{item.name}</div>
                          <div className="text-gray-500 text-[10px]">{item.region} ({tier})</div>
                        </td>
                        <td className="p-3">
                          <span className="px-2 py-1 rounded bg-gray-800 border border-gray-700 text-[10px]">{item.gpuType}</span>
                        </td>
                        <td className="p-3 text-right text-gray-400">${base.toFixed(2)}</td>
                        <td className="p-3 text-right text-gray-400">x{multiplier.toFixed(2)}</td>
                        <td className="p-3 text-right">
                          <span className={diff > 0 ? 'text-red-400' : 'text-green-400'}>
                            {diff > 0 ? '+' : ''}{diff.toFixed(3)}
                            {isSurge && <span className="ml-1 text-[9px] bg-red-900 text-red-200 px-1 rounded">{t.surge}</span>}
                          </span>
                        </td>
                        <td className="p-3 text-right font-bold text-white">${item.pricePerHour.toFixed(3)}</td>
                        <td className="p-3 text-right text-neon-blue">
                          {currency.symbol}{(item.pricePerHour * currency.rate).toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                 <div className="bg-purple-900/20 border border-purple-800 rounded-lg p-4 text-sm text-purple-200">
                  <strong>{t.sviFormula}</strong>
                  <div className="mt-2 font-mono text-xs">
                    {t.sviFormulaDesc}<br/>
                    {t.higherBetter}
                  </div>
                </div>
                <div className="bg-gray-800 border border-gray-700 rounded-lg p-4 text-sm text-gray-300">
                  <strong>{t.exchangeRateApplied}</strong> 1 USD = {currency.rate} {currency.code}
                </div>
              </div>

              <table className="w-full text-left text-xs text-gray-300">
                <thead className="text-gray-500 uppercase font-bold bg-gray-900/50 sticky top-0">
                  <tr>
                    <th className="p-3">{t.model}</th>
                    <th className="p-3 text-right">{t.input1M}</th>
                    <th className="p-3 text-right">{t.output1M}</th>
                    <th className="p-3 text-right">{t.total1M}</th>
                    <th className="p-3 text-right">{t.totalLocal} ({currency.code})</th>
                    <th className="p-3 text-right">{t.benchmark}</th>
                    <th className="p-3 text-right">{t.sviScore}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {tokenData.map((item, idx) => {
                    const totalUSD = item.inputCost + item.outputCost;
                    const totalLocal = totalUSD * currency.rate;
                    const svi = item.benchmark / Math.max(0.01, totalLocal);
                    
                    return (
                      <tr key={idx} className="hover:bg-white/5 transition-colors">
                        <td className="p-3 font-medium text-white">
                          <div>{item.model}</div>
                          <div className="text-gray-500 text-[10px]">{item.provider}</div>
                        </td>
                        <td className="p-3 text-right text-gray-400">${item.inputCost.toFixed(2)}</td>
                        <td className="p-3 text-right text-gray-400">${item.outputCost.toFixed(2)}</td>
                        <td className="p-3 text-right font-bold">${totalUSD.toFixed(2)}</td>
                        <td className="p-3 text-right text-gray-300">{currency.symbol}{totalLocal.toFixed(2)}</td>
                        <td className="p-3 text-right text-yellow-400">{item.benchmark.toFixed(1)}</td>
                        <td className="p-3 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-neon-purple font-bold text-sm">{svi.toFixed(2)}</span>
                            <div className="w-16 h-1 bg-gray-800 rounded-full overflow-hidden">
                              <div className="h-full bg-neon-purple" style={{ width: `${Math.min(100, svi)}%` }}></div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
