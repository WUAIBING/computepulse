
import React from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { HistoricalDataPoint, CurrencyConfig, Language, Theme } from '../types';
import { TRANSLATIONS } from '../translations';
import { THEME_COLORS, getThemeClasses } from '../theme';

interface TrendChartProps {
  data: HistoricalDataPoint[];
  title: string;
  lineColor: string;
  fillColor: string;
  yUnit: string;
  currency: CurrencyConfig;
  language: Language;
  theme: Theme;
}

export const TrendChart: React.FC<TrendChartProps> = ({ 
  data, 
  title, 
  lineColor, 
  fillColor,
  yUnit,
  currency,
  language,
  theme
}) => {
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);
  const colors = THEME_COLORS[theme];
  
  // Convert history data for display (keep original data pure)
  const chartData = data.map(d => ({
    ...d,
    displayPrice: d.price * currency.rate
  }));

  return (
    <div className={`w-full ${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-6 h-[300px]`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className={`text-lg font-bold ${themeClasses.text} flex items-center gap-2`}>
          <span className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: lineColor }}></span>
          {title}
        </h3>
        <span className={`text-xs ${themeClasses.textMuted} font-mono`}>
          {t.last60s} ({currency.code})
        </span>
      </div>

      <ResponsiveContainer width="100%" height="85%">
        <AreaChart data={chartData} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={`gradient-${title}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={lineColor} stopOpacity={0.3}/>
              <stop offset="95%" stopColor={lineColor} stopOpacity={0}/>
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
            stroke={colors.textMuted} 
            tick={{fontSize: 10}} 
            tickFormatter={(val) => `${currency.symbol}${val.toFixed(2)}`}
            tickLine={false}
            axisLine={false}
            domain={['auto', 'auto']}
            width={50}
          />
          <Tooltip 
            contentStyle={{ backgroundColor: colors.chartTooltipBg, borderColor: colors.chartTooltipBorder, color: colors.text }}
            cursor={{ stroke: theme === 'dark' ? '#ffffff20' : '#00000010' }}
            formatter={(val: number) => [`${currency.symbol}${val.toFixed(3)}`, yUnit]}
            labelStyle={{ color: colors.textMuted, marginBottom: '0.25rem' }}
          />
          <Area 
            type="monotone" 
            dataKey="displayPrice" 
            stroke={lineColor} 
            strokeWidth={2}
            fillOpacity={1} 
            fill={`url(#gradient-${title})`} 
            isAnimationActive={false} // Disable animation for smoother realtime updates
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};
