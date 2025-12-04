
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
import { HistoricalDataPoint, Language } from '../types';
import { TRANSLATIONS } from '../translations';

interface GridLoadChartProps {
  data: HistoricalDataPoint[];
  language: Language;
}

export const GridLoadChart: React.FC<GridLoadChartProps> = ({ data, language }) => {
  const [showInfo, setShowInfo] = useState(false);
  const t = TRANSLATIONS[language];

  return (
    <div className="w-full bg-panel-bg rounded-xl border border-gray-800 p-6 h-[400px] relative overflow-visible">
      <div className="flex justify-between items-start mb-6 z-20 relative">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          {t.gridLoadTrend}
          
          {/* Tooltip Icon */}
          <div 
            className="relative group"
            onMouseEnter={() => setShowInfo(true)}
            onMouseLeave={() => setShowInfo(false)}
          >
            <svg className="w-4 h-4 text-gray-400 cursor-help hover:text-neon-blue transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            
            {/* Tooltip Popup */}
            <div className={`absolute left-0 top-6 w-64 bg-black/95 border border-gray-700 p-3 rounded-lg shadow-2xl text-xs text-gray-300 transition-opacity duration-200 z-50 pointer-events-none ${showInfo ? 'opacity-100' : 'opacity-0'}`}>
              <div className="font-bold text-neon-blue mb-1">{t.totalPower}</div>
              <div className="mb-2">{t.gridLoadDesc}</div>
              <div className="font-mono bg-gray-900 p-1 rounded border border-gray-800 text-center mb-2">
                GW = (GPUs * TDP * PUE) / 10^9
              </div>
            </div>
          </div>
        </h3>

        <span className="text-xs text-gray-500 bg-gray-900 px-2 py-1 rounded border border-gray-800 animate-pulse">
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
          <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3a" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="#6b7280" 
            tick={{fontSize: 10}}
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            domain={['auto', 'auto']}
            stroke="#6b7280"
            tick={{fontSize: 10}}
            tickLine={false}
            axisLine={false}
            tickFormatter={(val) => `${val.toFixed(2)} ${language === 'CN' ? '吉瓦' : 'GW'}`}
            width={60}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: '#0a0a0f', borderColor: '#374151', color: '#fff' }}
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
