
import React from 'react';
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

interface AnnualDataPoint {
  year: string;
  value: number;
  source?: string;
}

interface AnnualBarChartProps {
  data: AnnualDataPoint[];
  title: string;
  barColor: string;
  yUnit: string;
  language: Language;
  theme: Theme;
}

export const AnnualBarChart: React.FC<AnnualBarChartProps> = ({ 
  data, 
  title, 
  barColor,
  yUnit,
  language,
  theme
}) => {
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);
  const colors = THEME_COLORS[theme];

  return (
    <div className={`w-full ${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-6 h-[400px] overflow-visible`}>
      <div className="flex justify-between items-start mb-4">
        <h3 className={`text-lg font-bold ${themeClasses.text} flex items-center gap-2`}>
          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: barColor }}></span>
          {title}
        </h3>
        <span className={`text-xs ${themeClasses.textMuted} font-mono`}>
          {language === 'CN' ? '历史年度数据' : 'Historical Annual Data'}
        </span>
      </div>

      <ResponsiveContainer width="100%" height="85%">
        <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={colors.chartGrid} vertical={false} />
          <XAxis 
            dataKey="year" 
            stroke={colors.textMuted} 
            tick={{fontSize: 12}}
            tickLine={false}
            axisLine={false}
            angle={0}
          />
          <YAxis 
            stroke={colors.textMuted} 
            tick={{fontSize: 10}} 
            tickFormatter={(val) => `${val}${yUnit}`}
            tickLine={false}
            axisLine={false}
            domain={[0, 'auto']}
            width={60}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: colors.chartTooltipBg, 
              borderColor: colors.chartTooltipBorder, 
              color: colors.text,
              borderRadius: '8px',
              padding: '8px 12px'
            }}
            cursor={{ fill: theme === 'dark' ? '#ffffff10' : '#00000005' }}
            formatter={(value: number) => [`${value.toFixed(1)}${yUnit}`, language === 'CN' ? '能耗' : 'Energy']}
            labelStyle={{ color: colors.textMuted, marginBottom: '4px', fontWeight: 'bold' }}
          />
          <Bar 
            dataKey="value" 
            fill={barColor}
            radius={[8, 8, 0, 0]}
            maxBarSize={60}
          >
            {data.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={barColor}
                opacity={0.7 + (index / data.length) * 0.3}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};
