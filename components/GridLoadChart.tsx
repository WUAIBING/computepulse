
import React, { useState, useEffect } from 'react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Cell
} from 'recharts';
import { Language, Theme } from '../types';
import { TRANSLATIONS } from '../translations';
import { THEME_COLORS, getThemeClasses } from '../theme';

interface YearlyEnergyData {
  year: string;
  twh: number;
  source?: string;
}

interface GridLoadChartProps {
  language: Language;
  theme: Theme;
}

export const GridLoadChart: React.FC<GridLoadChartProps> = ({ language, theme }) => {
  const [showInfo, setShowInfo] = useState(false);
  const [historicalData, setHistoricalData] = useState<YearlyEnergyData[]>([]);
  const [loading, setLoading] = useState(true);
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);
  const colors = THEME_COLORS[theme];

  useEffect(() => {
    const fetchHistoricalData = async () => {
      try {
        const baseUrl = import.meta.env.BASE_URL;
        const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
        const response = await fetch(`${cleanBaseUrl}data/energy_history.json`);
        
        if (response.ok) {
          const data = await response.json();
          setHistoricalData(data);
        } else {
          // Fallback data if fetch fails
          setHistoricalData([
            { year: '2018', twh: 12.5 },
            { year: '2019', twh: 18.2 },
            { year: '2020', twh: 29.3 },
            { year: '2021', twh: 45.8 },
            { year: '2022', twh: 68.4 },
            { year: '2023', twh: 95.2 },
            { year: '2024', twh: 120.5 },
            { year: '2025', twh: 150.0 }
          ]);
        }
      } catch (error) {
        console.error('[GridLoadChart] Error fetching historical data:', error);
        // Use fallback data
        setHistoricalData([
          { year: '2018', twh: 12.5 },
          { year: '2019', twh: 18.2 },
          { year: '2020', twh: 29.3 },
          { year: '2021', twh: 45.8 },
          { year: '2022', twh: 68.4 },
          { year: '2023', twh: 95.2 },
          { year: '2024', twh: 120.5 },
          { year: '2025', twh: 150.0 }
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchHistoricalData();
  }, []);

  // Color gradient for bars (darker to lighter orange)
  const getBarColor = (index: number, total: number) => {
    const intensity = 0.5 + (index / total) * 0.5; // 0.5 to 1.0
    return `rgba(249, 115, 22, ${intensity})`; // orange-500 with varying opacity
  };

  return (
    <div className={`w-full ${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-6 h-[400px] relative overflow-visible`}>
      <div className="flex justify-between items-start mb-6 z-20 relative">
        <h3 className={`text-lg font-bold ${themeClasses.text} flex items-center gap-2`}>
          {t.gridLoadTrend}
          
          {/* Tooltip Icon */}
          <div 
            className="relative overflow-visible"
            onMouseEnter={() => setShowInfo(true)}
            onMouseLeave={() => setShowInfo(false)}
          >
            <svg className={`w-4 h-4 ${themeClasses.textMuted} cursor-help hover:text-neon-blue transition-colors`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            
            {/* Tooltip Popup */}
            <div className={`absolute left-1/2 -translate-x-1/2 md:left-0 md:translate-x-0 bottom-full mb-2 w-64 max-w-[calc(100vw-2rem)] ${theme === 'dark' ? 'bg-black/95 border-gray-700 text-gray-300' : 'bg-white border-gray-300 text-gray-700 shadow-xl'} border p-3 rounded-lg shadow-2xl text-xs transition-opacity duration-200 z-50 pointer-events-none ${showInfo ? 'opacity-100' : 'opacity-0'}`}>
              <div className="font-bold text-neon-blue mb-1">{language === 'CN' ? '历史能耗数据' : 'Historical Energy Data'}</div>
              <div className="mb-2">{language === 'CN' ? '全球AI数据中心年度总能耗（太瓦时）' : 'Global AI datacenter annual energy consumption (TWh)'}</div>
              <div className={`font-mono ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-300'} p-1 rounded border text-center mb-2`}>
                {language === 'CN' ? '数据来源：AI联网搜索' : 'Source: AI Web Search'}
              </div>
            </div>
          </div>
        </h3>

        <span className={`text-xs ${themeClasses.textMuted} ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-300'} px-2 py-1 rounded border`}>
          📊 {language === 'CN' ? '历史数据' : 'Historical Data'}
        </span>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-[300px]">
          <div className={`text-sm ${themeClasses.textMuted}`}>
            {language === 'CN' ? '加载中...' : 'Loading...'}
          </div>
        </div>
      ) : (
        <ResponsiveContainer width="100%" height="85%">
          <BarChart data={historicalData} margin={{ top: 10, right: 10, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.chartGrid} vertical={false} />
            <XAxis 
              dataKey="year" 
              stroke={colors.textMuted} 
              tick={{fontSize: 11}}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke={colors.textMuted}
              tick={{fontSize: 10}}
              tickLine={false}
              axisLine={false}
              tickFormatter={(val) => `${val} ${language === 'CN' ? '太瓦时' : 'TWh'}`}
              width={70}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: colors.chartTooltipBg, borderColor: colors.chartTooltipBorder, color: colors.text }}
              cursor={{ fill: theme === 'dark' ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)' }}
              formatter={(value: number) => [`${value.toFixed(1)} ${language === 'CN' ? '太瓦时' : 'TWh'}`, language === 'CN' ? '年度能耗' : 'Annual Energy']}
            />
            <Bar 
              dataKey="twh" 
              radius={[8, 8, 0, 0]}
              isAnimationActive={true}
              animationDuration={800}
            >
              {historicalData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(index, historicalData.length)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};
