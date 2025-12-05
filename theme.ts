import { Theme, ThemeColors } from './types';

export const THEME_COLORS: Record<Theme, ThemeColors> = {
  dark: {
    bg: '#0a0a0f',
    panelBg: '#13131a',
    border: '#1f2937',
    text: '#ffffff',
    textSecondary: '#e0e0e0',
    textMuted: '#9ca3af',
    accent: '#3b82f6',
    accentHover: '#2563eb',
    chartGrid: '#2d2d3a',
    chartTooltipBg: '#0a0a0f',
    chartTooltipBorder: '#374151',
  },
  light: {
    bg: '#f8fafc',
    panelBg: '#ffffff',
    border: '#e2e8f0',
    text: '#0f172a',
    textSecondary: '#334155',
    textMuted: '#64748b',
    accent: '#3b82f6',
    accentHover: '#2563eb',
    chartGrid: '#e2e8f0',
    chartTooltipBg: '#ffffff',
    chartTooltipBorder: '#cbd5e1',
  },
};

export const getThemeClasses = (theme: Theme) => {
  if (theme === 'light') {
    return {
      bg: 'bg-gray-50',
      panelBg: 'bg-white',
      border: 'border-gray-200',
      text: 'text-gray-900',
      textSecondary: 'text-gray-700',
      textMuted: 'text-gray-500',
      hoverBg: 'hover:bg-gray-100',
      activeBg: 'bg-gray-100',
    };
  }
  
  return {
    bg: 'bg-[#0a0a0f]',
    panelBg: 'bg-panel-bg',
    border: 'border-gray-800',
    text: 'text-white',
    textSecondary: 'text-gray-300',
    textMuted: 'text-gray-500',
    hoverBg: 'hover:bg-gray-800',
    activeBg: 'bg-gray-800',
  };
};
