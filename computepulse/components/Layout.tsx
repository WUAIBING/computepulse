
import React from 'react';
import { Language, Theme } from '../types';
import { TRANSLATIONS } from '../translations';
import { getThemeClasses } from '../theme';

interface LayoutProps {
  children: React.ReactNode;
  language: Language;
  theme: Theme;
  onThemeToggle: () => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, language, theme, onThemeToggle }) => {
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);

  return (
    <div className={`min-h-screen ${themeClasses.bg} ${themeClasses.textSecondary} font-sans ${theme === 'dark' ? 'selection:bg-neon-blue selection:text-black' : 'selection:bg-blue-200 selection:text-gray-900'}`}>
      <nav className={`border-b ${themeClasses.border} ${theme === 'dark' ? 'bg-black/50' : 'bg-white/80'} backdrop-blur-md sticky top-0 z-50`}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <button
                onClick={onThemeToggle}
                className="w-8 h-8 bg-gradient-to-br from-neon-blue to-neon-purple rounded flex items-center justify-center hover:scale-110 active:scale-95 transition-transform cursor-pointer group"
                title={theme === 'dark' ? (language === 'CN' ? '切换到亮色模式' : 'Switch to Light Mode') : (language === 'CN' ? '切换到暗色模式' : 'Switch to Dark Mode')}
                aria-label="Toggle theme"
              >
                <svg className="w-5 h-5 text-white group-hover:rotate-12 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </button>
              <span className={`text-xl font-bold tracking-tighter ${themeClasses.text}`}>
                {language === 'CN' ? (
                  <>算力<span className="text-neon-blue">脉搏</span></>
                ) : (
                  <>Compute<span className="text-neon-blue">Pulse</span></>
                )}
              </span>
            </div>
            <div className="hidden md:flex items-center gap-6">
              {/* Data Source Indicator */}
              <div className="flex flex-col items-end">
                <div className="flex items-center gap-2">
                   <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                   <span className={`text-[10px] uppercase font-bold ${themeClasses.textMuted} tracking-wider`}>{t.dataSource}</span>
                </div>
                <div className={`text-xs ${themeClasses.textMuted}`}>
                  {t.dataSourceDesc}
                </div>
              </div>
              
              <div className={`h-8 w-px ${themeClasses.border}`}></div>

              <div className="flex items-baseline space-x-4">
                <span className={`px-3 py-1 rounded-full text-xs font-medium ${theme === 'dark' ? 'bg-green-900/30 text-neon-green border border-green-900' : 'bg-green-50 text-green-700 border border-green-200'}`}>
                  ● {t.systemOperational}
                </span>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};
