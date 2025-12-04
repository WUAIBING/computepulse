
import React, { useState } from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';
import { HistoricalDataPoint, Language, Theme } from '../types';
import { TRANSLATIONS } from '../translations';
import { THEME_COLORS, getThemeClasses } from '../theme';

interface GridLoadChartProps {
  data: HistoricalDataPoint[];
  language: Language;
  theme: Theme;
}

export const GridLoadChart: React.FC<GridLoadChartProps> = ({ data, language, theme }) => {
  const [showInfo, setShowInfo] = useState(false);
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);
  const colors = THEME_COLORS[theme];

  return (
    <div className={`w-full ${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-6 h-[400px] relative overflow-visible`}>
      <div className="flex justify-between items-start mb-6 z-20 relative">
        <h3 className={`text-lg font-bold ${themeClasses.text} flex items-center gap-2`}>
          {t.gridLoadTrend}
          
          {/* Tooltip Icon */}
          <div 
            className="relative group"
            onMouseEnter={() => setShowInfo(true)}
            onMouseLeave={() => setShowInfo(false)}
          >
            <svg className={`w-4 h-4 ${themeClasses.textMuted} cursor-help hover:text-neon-blue transition-colors`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            
            {/* Tooltip Popup */}
            <div className={`absolute left-1/2 -translate-x-1/2 md:left-0 md:translate-x-0 top-6 w-64 max-w-[calc(100vw-2rem)] ${theme === 'dark' ? 'bg-black/95 border-gray-700 text-gray-300' : 'bg-white border-gray-300 text-gray-700 shadow-xl'} border p-3 rounded-lg shadow-2xl text-xs transition-opacity duration-200 z-50 pointer-events-none ${showInfo ? 'opacity-100' : 'opacity-0'}`}>
              <div className="font-bold text-neon-blue mb-1">{t.totalPower}</div>
              <div className="mb-2">{t.gridLoadDesc}</div>
              <div className={`font-mono ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-300'} p-1 rounded border text-center mb-2`}>
                GW = (GPUs * TDP * PUE) / 10^9
              </div>
            </div>
          </div>
        </h3>

        <span className={`text-xs ${themeClasses.textMuted} ${theme === 'dark' ? 'bg-gray-900 border-gray-800' : 'bg-gray-100 border-gray-300'} px-2 py-1 rounded border animate-pulse`}>
          ● {t.realTime}
        </span>
      </div>

      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={data} margin={{ left: 0, right: 0 }}>
          <defs>
            <linearGradient id="colorPower" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.chartGrid} vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke={colors.textMuted} 
            tick={{fontSize: 10}}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            domain={['auto', 'auto']}
            stroke={colors.textMuted}
            tick={{fontSize: 10}}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${val.toFixed(2)} ${language === 'CN' ? '吉瓦' : 'GW'}`}
            width={60}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: colors.chartTooltipBg, borderColor: colors.chartTooltipBorder, color: colors.text }}
            itemStyle={{ color: '#f59e0b' }}
            cursor={{ stroke: '#f59e0b', strokeWidth: 1, strokeDasharray: '5 5' }}
            formatter={(value: number) => [`${value.toFixed(4)} ${language === 'CN' ? '吉瓦' : 'GW'}`, t.totalPower]}
          />
          <Area 
            type="monotone" 
            dataKey="price" 
            stroke="#f59e0b" 
            strokeWidth={2}
            fillOpacity={1} 
            fill="url(#colorPower)" 
            isAnimationActive={false}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
