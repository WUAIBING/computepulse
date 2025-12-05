
import React from 'react';
import { Language } from '../types';
import { TRANSLATIONS } from '../translations';

interface LayoutProps {
  children: React.ReactNode;
  language: Language;
}

export const Layout: React.FC<LayoutProps> = ({ children, language }) => {
  const t = TRANSLATIONS[language];

  return (
    <div className="min-h-screen bg-dark-bg text-gray-200 font-sans selection:bg-neon-blue selection:text-black">
      <nav className="border-b border-gray-800 bg-black/50 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-gradient-to-br from-neon-blue to-neon-purple rounded flex items-center justify-center">
                <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <span className="text-xl font-bold tracking-tighter text-white">
                {language === 'CN' ? (
                  <>算力<span className="text-neon-blue">脉搏</span></>
                ) : (
                  <>Compute<span className="text-neon-blue">Pulse</span></>
                )}
              </span>
            </div>
            <div className="flex items-center gap-4">
              {/* Mobile data indicator */}
              <div className="md:hidden flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-xs text-gray-400">{t.dataSourceShort || t.dataSource}</span>
              </div>

              {/* Desktop data source indicator */}
              <div className="hidden md:flex items-center gap-6">
                <div className="flex flex-col items-end">
                  <div className="flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                    <span className="text-[10px] uppercase font-bold text-gray-400 tracking-wider">{t.dataSource}</span>
                  </div>
                  <div className="text-xs text-gray-400">
                    {t.dataSourceDesc}
                  </div>
                </div>

                <div className="h-8 w-px bg-gray-800"></div>

                <div className="flex items-baseline space-x-4">
                  <span className="px-3 py-1 rounded-full text-xs font-medium bg-green-900/30 text-neon-green border border-green-900">
                    ● {t.systemOperational}
                  </span>
                </div>
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
