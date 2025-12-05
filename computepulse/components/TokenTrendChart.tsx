
import React from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { HistoricalDataPoint, CurrencyConfig, Language } from '../types';
import { TRANSLATIONS } from '../translations';

interface TokenTrendChartProps {
  data: HistoricalDataPoint[];
  currency?: CurrencyConfig;
  language?: Language;
  lineColor?: string;
  fillColor?: string;
  height?: string;
  showXAxis?: boolean;
  showYAxis?: boolean;
}

export const TokenTrendChart: React.FC<TokenTrendChartProps> = ({ 
  data, 
  currency, 
  language,
  lineColor = "#bc13fe",
  fillColor = "#bc13fe",
  showXAxis = false,
  showYAxis = false
}) => {
  // Safe access to translation
  const t = (language && TRANSLATIONS[language]) ? TRANSLATIONS[language] : {};
  const title = t.tokenPriceIndex || "Token Price Index";
  const symbol = currency ? currency.symbol : "$";
  const rate = currency ? currency.rate : 1;

  return (
    <div className="w-full h-full min-h-[10px] flex flex-col justify-center">
      {language && currency && (
        <div className="text-xs text-gray-400 mb-2 font-bold flex justify-between">
          <span>{title}</span>
          <span className="text-neon-purple">{symbol} / 1M</span>
        </div>
      )}
      <div className="flex-grow h-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <defs>
              <linearGradient id={`gradient-${lineColor}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={lineColor} stopOpacity={0.3}/>
                <stop offset="95%" stopColor={lineColor} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#2d2d3a" vertical={false} />
            <XAxis 
              dataKey="time" 
              hide={true}
            />
            <YAxis 
              domain={['auto', 'auto']}
              hide={true}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#0a0a0f', borderColor: '#374151', color: '#fff', fontSize: '12px' }}
              itemStyle={{ color: lineColor }}
              formatter={(value: number) => [`${symbol}${(value * rate).toFixed(3)}`, 'Value']}
              labelStyle={{ display: 'none' }}
            />
            <Line 
              type="monotone" 
              dataKey="price" 
              stroke={lineColor} 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: lineColor }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
