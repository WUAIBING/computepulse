
import React, { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { TrendChart } from './components/TrendChart';
import { MarketVitals } from './components/MarketVitals';
import { MacroDashboard } from './components/MacroDashboard';
import { CalculationModal } from './components/CalculationModal';
import { GridLoadChart } from './components/GridLoadChart';
import { generateMockData, generateMockTokenData, CURRENCIES, MACRO_CONSTANTS } from './constants';
import { ComputeProvider, TokenProvider, HistoricalDataPoint, CurrencyCode, Language } from './types';
import { TRANSLATIONS } from './translations';

type ViewMode = 'COMPUTE' | 'TOKENS' | 'GRID_LOAD';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('COMPUTE');
  const [data, setData] = useState<ComputeProvider[]>([]);
  const [tokenData, setTokenData] = useState<TokenProvider[]>([]);
  
  // Currency & Language State
  const [currencyCode, setCurrencyCode] = useState<CurrencyCode>('USD');
    const [language, setLanguage] = useState<Language>('CN');
    
    const currency = CURRENCIES.find(c => c.code === currencyCode) || CURRENCIES[0];
  const t = TRANSLATIONS[language];

  // History State
  const [computeHistory, setComputeHistory] = useState<HistoricalDataPoint[]>([]);
  const [tokenHistory, setTokenHistory] = useState<HistoricalDataPoint[]>([]);
  const [gridLoadHistory, setGridLoadHistory] = useState<HistoricalDataPoint[]>([]);

  // Derived Metrics
  const [cvix, setCvix] = useState<number>(0);
  // Macro Metrics
  const [activeGpus, setActiveGpus] = useState<number>(MACRO_CONSTANTS.EST_GLOBAL_ACTIVE_GPUS);
  const [kwhPrice, setKwhPrice] = useState<number>(MACRO_CONSTANTS.GLOBAL_KWH_PRICE);
  const [annualTWh, setAnnualTWh] = useState<number>(0); // New state
  const [avgSpotPriceUSD, setAvgSpotPriceUSD] = useState<number>(0);

  const [showCalcModal, setShowCalcModal] = useState(false);
  const [calcModalTab, setCalcModalTab] = useState<'GPU' | 'TOKEN'>('GPU');

  // Auto-detect Language (Default to CN)
  useEffect(() => {
    const browserLang = navigator.language || navigator.languages[0];
    if (browserLang.toLowerCase().includes('zh')) {
      setLanguage('CN');
      setCurrencyCode('CNY');
    } else {
      setLanguage('EN');
      setCurrencyCode('USD');
    }
  }, []);

  // Initialize Data
  useEffect(() => {
    const fetchRealData = async () => {
      try {
        // 1. Fetch GPU Prices
        // Use special Vite public path resolution
        // In Vite/GH Pages, files in 'public/data' are served at '/computepulse/data/...' or './data/...'
        // We'll try a robust approach: use import.meta.env.BASE_URL
        const baseUrl = import.meta.env.BASE_URL;

        // Debug logging for GitHub Pages troubleshooting
        console.log('[ComputePulse] Base URL:', baseUrl);
        console.log('[ComputePulse] Environment mode:', import.meta.env.MODE);

        // Ensure baseUrl ends with '/'
        const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
        console.log('[ComputePulse] Clean base URL for data fetching:', cleanBaseUrl);
        
        console.log(`[ComputePulse] Fetching GPU prices from: ${cleanBaseUrl}data/gpu_prices.json`);
        const gpuResponse = await fetch(`${cleanBaseUrl}data/gpu_prices.json`);

        if (gpuResponse.ok) {
          console.log(`[ComputePulse] GPU prices loaded successfully, status: ${gpuResponse.status}`);
          const realPrices = await gpuResponse.json();
          console.log(`[ComputePulse] GPU prices data count: ${realPrices?.length || 0}`);

          if (realPrices && realPrices.length > 0) {
            const mappedData: ComputeProvider[] = realPrices.map((item: any, index: number) => ({
              id: `real-${index}`,
              name: item.provider,
              tier: 'Standard',
              pricePerHour: item.price,
              region: item.region || 'Global',
              reliability: 99.9,
              type: item.gpu.includes('H100') ? 'H100' : (item.gpu.includes('A100') ? 'A100' : 'Other'),
              specs: { vram: '80GB' }
            }));
            const validatedData = mappedData.filter(d => !isNaN(d.pricePerHour) && d.pricePerHour > 0);
            console.log(`[ComputePulse] Valid GPU data items: ${validatedData.length}`);

            if (validatedData.length > 0) {
              setData(validatedData);
              console.log('[ComputePulse] GPU data set successfully');
            } else {
              console.warn('[ComputePulse] No valid GPU data after validation');
              setData(generateMockData());
            }
          } else {
            console.warn('[ComputePulse] GPU prices data empty or invalid');
            setData(generateMockData());
          }
        } else {
          console.error(`[ComputePulse] Failed to load GPU prices: ${gpuResponse.status} ${gpuResponse.statusText}`);
          setData(generateMockData());
        }

        // 2. Fetch Token Prices
        console.log(`[ComputePulse] Fetching token prices from: ${cleanBaseUrl}data/token_prices.json`);
        const tokenResponse = await fetch(`${cleanBaseUrl}data/token_prices.json`);

        if (tokenResponse.ok) {
            console.log(`[ComputePulse] Token prices loaded successfully, status: ${tokenResponse.status}`);
            const realTokens = await tokenResponse.json();
            console.log(`[ComputePulse] Token prices data count: ${realTokens?.length || 0}`);

            if (realTokens && realTokens.length > 0) {
                const mappedTokens: TokenProvider[] = realTokens.map((item: any, index: number) => ({
                    id: `token-${index}`,
                    name: item.model,
                    provider: item.provider,
                    inputCost: item.input_price,
                    outputCost: item.output_price,
                    latency: Math.floor(Math.random() * 50) + 20, // Latency is hard to scrape, keeping mock
                    contextWindow: '128k', // Hard to scrape reliably without complex parsing
                    mmluScore: 85 + Math.random() * 5 // Mocking benchmark for now
                }));
                setTokenData(mappedTokens);
                console.log('[ComputePulse] Token data set successfully');
            } else {
                console.warn('[ComputePulse] Token prices data empty or invalid');
                setTokenData(generateMockTokenData());
            }
        } else {
            console.error(`[ComputePulse] Failed to load token prices: ${tokenResponse.status} ${tokenResponse.statusText}`);
            setTokenData(generateMockTokenData());
        }

        // 3. Fetch Grid Load
        console.log(`[ComputePulse] Fetching grid load from: ${cleanBaseUrl}data/grid_load.json`);
        const gridResponse = await fetch(`${cleanBaseUrl}data/grid_load.json`);

        if (gridResponse.ok) {
           console.log(`[ComputePulse] Grid load loaded successfully, status: ${gridResponse.status}`);
           const gridData = await gridResponse.json();
           console.log("[ComputePulse] Grid data:", gridData);

           if (gridData) {
             if (gridData.active_gpu_est) {
               setActiveGpus(gridData.active_gpu_est);
               console.log(`[ComputePulse] Active GPUs set: ${gridData.active_gpu_est}`);
             }
             if (gridData.kwh_price) {
               setKwhPrice(gridData.kwh_price);
               console.log(`[ComputePulse] kWh price set: ${gridData.kwh_price}`);
             }
             if (gridData.annual_twh) {
               setAnnualTWh(gridData.annual_twh);
               console.log(`[ComputePulse] Annual TWh set: ${gridData.annual_twh}`);
             }
           } else {
             console.warn('[ComputePulse] Grid load data is null or undefined');
           }
        } else {
          console.error(`[ComputePulse] Failed to load grid load: ${gridResponse.status} ${gridResponse.statusText}`);
        }

      } catch (e) {
        console.error("[ComputePulse] Critical error fetching real data:", e);
        console.warn("[ComputePulse] Falling back to mock data due to critical error");
        setData(generateMockData());
        setTokenData(generateMockTokenData());
      }
    };

    fetchRealData();
  }, []);

  // Simulate Live Updates & History Tracking
  useEffect(() => {
    const interval = setInterval(() => {
      const now = new Date();
      const timeLabel = now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute:'2-digit', second:'2-digit' });

      // 1. Update Compute Data
      setData(prevData => {
        const newData = prevData.map(item => {
          if (Math.random() > 0.7) {
            const change = (Math.random() * 0.1) - 0.05;
            return {
              ...item,
              pricePerHour: Math.max(0.1, parseFloat((item.pricePerHour + change).toFixed(3))),
              lastUpdated: now.toISOString()
            };
          }
          return item;
        });

        const avgPrice = newData.length > 0 ? newData.reduce((acc, c) => acc + c.pricePerHour, 0) / newData.length : 0;
        setAvgSpotPriceUSD(avgPrice); 
        
        const prices = newData.map(d => d.pricePerHour);
        const mean = prices.length > 0 ? prices.reduce((a, b) => a + b, 0) / prices.length : 0;
        const variance = prices.length > 0 ? prices.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / prices.length : 0;
        const stdDev = Math.sqrt(variance);
        const calculatedCvix = mean > 0 ? (stdDev / mean) * 100 : 0;
        
        setCvix(calculatedCvix);

        setComputeHistory(prev => {
          const newHistory = [...prev, { time: timeLabel, price: avgPrice }];
          return newHistory.slice(-20);
        });

        return newData;
      });

      // 2. Update Token Data
      setTokenData(prevData => {
         const newData = prevData.map(item => {
           if (Math.random() > 0.9) {
             const change = (Math.random() * 0.05) - 0.025;
             return {
               ...item,
               inputCost: parseFloat((item.inputCost + change).toFixed(4)),
               lastUpdated: now.toISOString()
             }
           }
           return item;
         });

         const avgInputCost = newData.reduce((acc, t) => acc + t.inputCost, 0) / newData.length;
         
         setTokenHistory(prev => {
            const newHistory = [...prev, { time: timeLabel, price: avgInputCost }];
            return newHistory.slice(-20);
         });

         return newData;
      });

      // 3. Fluctuate Active GPU Count
      setActiveGpus(prev => {
         // const fluctuation = Math.floor((Math.random() * 1000) - 500); 
         // const newCount = prev + fluctuation;
         const newCount = prev; // Keep stable for now, using real data
         
         // Calculate Grid Load (GW)
         // Watts = Count * Avg TDP * PUE
         // GW = Watts / 1e9
         const totalWatts = newCount * MACRO_CONSTANTS.AVG_TDP_WATTS * MACRO_CONSTANTS.GLOBAL_PUE;
         const gw = totalWatts / 1e9;

         setGridLoadHistory(prevHist => {
            const newHistory = [...prevHist, { time: timeLabel, price: gw }];
            return newHistory.slice(-20);
         });

         return newCount;
      });

    }, 3000); 

    return () => clearInterval(interval);
  }, []);

  const dominanceData = [
    { name: 'NVIDIA H100', pct: 40 },
    { name: 'NVIDIA A100', pct: 25 },
    { name: 'Huawei Ascend', pct: 15 },
    { name: 'Cambricon/Others', pct: 20 }
  ];

  return (
    <Layout language={language}>
      <div className="space-y-6">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row justify-between items-center gap-4 pb-2 border-b border-gray-800">
          <div>
            <div className="flex flex-wrap gap-4 text-sm items-center">
              <button 
                onClick={() => setViewMode('COMPUTE')}
                className={`px-3 py-1 rounded transition-all ${viewMode === 'COMPUTE' ? 'bg-neon-blue text-black font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                {t.viewGpu}
              </button>
              <button 
                 onClick={() => setViewMode('TOKENS')}
                 className={`px-3 py-1 rounded transition-all ${viewMode === 'TOKENS' ? 'bg-neon-purple text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                {t.viewToken}
              </button>
              <button 
                 onClick={() => setViewMode('GRID_LOAD')}
                 className={`px-3 py-1 rounded transition-all ${viewMode === 'GRID_LOAD' ? 'bg-orange-500 text-white font-bold' : 'text-gray-400 hover:text-white'}`}
              >
                {t.viewGridLoad}
              </button>

              {/* Currency & Language Switcher */}
              <div className="flex flex-wrap items-center gap-2">
                <div className="flex items-center bg-gray-900 rounded border border-gray-800">
                  <span className="text-gray-500 px-2 text-xs">{t.unit}</span>
                  <select 
                    value={currencyCode} 
                    onChange={(e) => setCurrencyCode(e.target.value as CurrencyCode)}
                    className="bg-transparent text-white text-xs font-mono font-bold py-1 pr-2 focus:outline-none cursor-pointer"
                  >
                    {CURRENCIES.map((c) => (
                      <option key={c.code} value={c.code} className="bg-gray-900">{c.code} ({c.symbol})</option>
                    ))}
                  </select>
                </div>

                {/* Language Toggle */}
                <div className="flex bg-gray-900 rounded border border-gray-800 p-0.5">
                  <button 
                    onClick={() => { setLanguage('CN'); setCurrencyCode('CNY'); }}
                    className={`px-2 py-0.5 text-xs font-bold rounded ${language === 'CN' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
                  >
                    中文
                  </button>
                  <button 
                    onClick={() => { setLanguage('EN'); setCurrencyCode('USD'); }}
                    className={`px-2 py-0.5 text-xs font-bold rounded ${language === 'EN' ? 'bg-gray-700 text-white' : 'text-gray-500 hover:text-gray-300'}`}
                  >
                    EN
                  </button>
                </div>

                {/* Verify Data Button - Mobile Optimized */}
                <button
                  onClick={() => setShowCalcModal(true)}
                  className="px-3 py-1.5 min-h-[32px] bg-gray-900 hover:bg-gray-800 text-gray-400 hover:text-white text-xs font-medium rounded border border-gray-800 hover:border-gray-700 transition-all duration-200 flex items-center gap-1.5 active:scale-95 touch-manipulation"
                  title={t.verifyData}
                  aria-label={t.verifyData}
                >
                  <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                  <span className="whitespace-nowrap">{t.verifyData}</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* NEW MACRO DASHBOARD */}
        <MacroDashboard 
          avgSpotPrice={avgSpotPriceUSD} 
          activeGpus={activeGpus} 
          tokenHistory={tokenHistory}
          kwhPrice={kwhPrice}
          annualTWh={annualTWh}
          currency={currency}
          language={language}
        />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          
          {/* Main Content Column */}
          <div className="lg:col-span-8 space-y-6">
            
            {viewMode === 'COMPUTE' && (
              <>
                 {/* 1. Trend Chart */}
                 <TrendChart 
                    data={computeHistory} 
                    title={t.gpuIndexTitle} 
                    lineColor="#FFD700"
                    fillColor="#FFD700"
                    yUnit={` / ${language === 'CN' ? '小时' : 'hr'}`}
                    currency={currency}
                    language={language}
                 />
              </>
            )}

            {viewMode === 'TOKENS' && (
              <>
                 {/* Token View */}
                 <TrendChart 
                    data={tokenHistory} 
                    title={language === 'EN' ? "Token Cost Index Trend" : "Token 成本指数趋势"} 
                    lineColor="#bc13fe"
                    fillColor="#bc13fe"
                    yUnit=" / 1M"
                    currency={currency}
                    language={language}
                 />
              </>
            )}

            {viewMode === 'GRID_LOAD' && (
              <div className="space-y-6">
                <GridLoadChart data={gridLoadHistory} language={language} />
                
                {/* Reusing MacroDashboard components or custom stats for Grid Load */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <div className="bg-panel-bg p-6 rounded-xl border border-gray-800">
                      <h3 className="text-gray-400 text-sm mb-2">{t.estActiveGpus}</h3>
                      <div className="text-3xl font-bold text-white">{activeGpus.toLocaleString()}</div>
                      <div className="text-neon-blue text-xs mt-1">Global Data Centers</div>
                   </div>
                   <div className="bg-panel-bg p-6 rounded-xl border border-gray-800">
                      <h3 className="text-gray-400 text-sm mb-2">{t.globalEnergyRate}</h3>
                      <div className="text-3xl font-bold text-white">
                        {currency.symbol}{(kwhPrice * currency.rate).toFixed(3)} / kWh
                      </div>
                      <div className="text-gray-500 text-xs mt-1">Weighted Industrial Average</div>
                   </div>
                </div>
              </div>
            )}
            
          </div>

          {/* Sidebar Column */}
          <div className="lg:col-span-4 flex flex-col gap-6">
            <MarketVitals cvix={cvix} currency={currency} language={language} kwhPrice={kwhPrice} />
          </div>

        </div>
      </div>
      <CalculationModal 
        isOpen={showCalcModal}
        onClose={() => setShowCalcModal(false)}
        computeData={data}
        tokenData={tokenData}
        currency={currency}
        language={language}
        activeTab={calcModalTab}
        onTabChange={setCalcModalTab}
      />
    </Layout>
  );
}

export default App;
