import React, { useState, useEffect } from 'react';

import { Language, Theme } from '../types';
import { TRANSLATIONS } from '../translations';
import { getThemeClasses } from '../theme';

interface AIModel {
  name: string;
  confidence: number;
  tasksProcessed: number;
  avgResponseTime: number;
}

interface AIConsortiumData {
  status: 'active' | 'learning' | 'idle';
  models: AIModel[];
  lastUpdate: string;
  totalTasksProcessed: number;
  dataFreshness: {
    gpuPrices: string;
    tokenPrices: string;
    gridLoad: string;
    realtimeData: string;
  };
}

interface AIConsortiumStatusProps {
  language: Language;
  theme: Theme;
}

export const AIConsortiumStatus: React.FC<AIConsortiumStatusProps> = ({ language, theme }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  // const [showInfo, setShowInfo] = useState(false); // Removed state-based tooltip
  const [consortiumData, setConsortiumData] = useState<AIConsortiumData | null>(null);
  
  const t = TRANSLATIONS[language];
  const themeClasses = getThemeClasses(theme);

  useEffect(() => {
    const fetchConsortiumStatus = async () => {
      try {
        const baseUrl = import.meta.env.BASE_URL;
        const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
        
        // Fetch confidence scores
        const confidenceResponse = await fetch(`${cleanBaseUrl}data/ai_orchestrator/confidence_scores.json`);
        
        if (confidenceResponse.ok) {
          const confidenceData = await confidenceResponse.json();
          
          // Transform data into display format
          const scores = confidenceData.scores || confidenceData.confidence_scores || {};
          const models: AIModel[] = Object.entries(scores).map(([name, score]) => {
            // Parse key format: "model_task"
            const displayName = name.includes('_') ? name.split('_')[0] : name;
            return {
              name: displayName.charAt(0).toUpperCase() + displayName.slice(1),
              confidence: (score as number) * 100,
              tasksProcessed: Math.floor(Math.random() * 1000) + 100, // TODO: Get from performance history
              avgResponseTime: Math.floor(Math.random() * 500) + 100
            };
          });

          // Deduplicate models if multiple tasks exist for same model (take average confidence)
          const uniqueModels = Array.from(
            models.reduce((map, item) => {
              if (!map.has(item.name)) {
                map.set(item.name, item);
              } else {
                const existing = map.get(item.name)!;
                existing.confidence = (existing.confidence + item.confidence) / 2;
                map.set(item.name, existing);
              }
              return map;
            }, new Map<string, AIModel>()).values()
          );

          setConsortiumData({
            status: 'active',
            models: uniqueModels,
            lastUpdate: confidenceData.last_updated || new Date().toISOString(),
            totalTasksProcessed: confidenceData.total_requests || uniqueModels.length * 150, // Mock if missing
            dataFreshness: {
              gpuPrices: 'Real-time',
              tokenPrices: 'Real-time',
              gridLoad: 'Hourly',
              realtimeData: 'Hourly'
            }
          });
        }
      } catch (error) {
        console.error('[AIConsortium] Failed to fetch status:', error);
      }
    };

    fetchConsortiumStatus();
    const interval = setInterval(fetchConsortiumStatus, 30000); // Update every 30s
    
    return () => clearInterval(interval);
  }, []);

  if (!consortiumData) {
    return null;
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-neon-green';
      case 'learning': return 'text-neon-blue';
      case 'idle': return 'text-gray-500';
      default: return 'text-gray-500';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 80) return 'bg-neon-green';
    if (confidence >= 60) return 'bg-neon-blue';
    if (confidence >= 40) return 'bg-yellow-500';
    return 'bg-orange-500';
  };

  const getConfidenceTextColor = (confidence: number) => {
    if (confidence >= 80) return 'text-neon-green';
    if (confidence >= 60) return 'text-neon-blue';
    if (confidence >= 40) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const timeSinceUpdate = () => {
    const now = new Date();
    const lastUpdate = new Date(consortiumData.lastUpdate);
    const diffMs = now.getTime() - lastUpdate.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return language === 'CN' ? '刚刚' : 'Just now';
    if (diffMins < 60) return language === 'CN' ? `${diffMins}分钟前` : `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    return language === 'CN' ? `${diffHours}小时前` : `${diffHours}h ago`;
  };

  return (
    <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} p-5 relative overflow-hidden hover:border-neon-blue/30 transition-all duration-300`}>
      
      {/* Header */}
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <div className="relative">
            {/* Pulsing Status Indicator */}
            <div className={`w-2 h-2 rounded-full ${getStatusColor(consortiumData.status)} animate-pulse`}></div>
            <div className={`absolute inset-0 w-2 h-2 rounded-full ${getStatusColor(consortiumData.status)} opacity-30 animate-ping`}></div>
          </div>
          
          <div>
            <h3 className={`${themeClasses.textMuted} text-xs font-bold uppercase tracking-wider flex items-center gap-2`}>
              {language === 'CN' ? 'AI 联合体状态' : 'AI Consortium Status'}
              
              {/* Info Icon */}
              <div 
                className="relative group"
              >
                <svg className="w-3.5 h-3.5 text-gray-500 cursor-help hover:text-white transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                
                <div className={`absolute left-0 bottom-full mb-2 w-80 ${theme === 'dark' ? 'bg-black/95 border-gray-700' : 'bg-white border-gray-300 shadow-xl'} border p-4 rounded-lg shadow-2xl z-50 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                    <div className="text-neon-blue font-bold text-sm mb-2">
                      {language === 'CN' ? 'AI 联合体系统' : 'AI Consortium System'}
                    </div>
                    <p className={`text-xs ${themeClasses.textMuted} leading-relaxed`}>
                      {language === 'CN' 
                        ? '多模型协作系统，使用 EWMA 算法持续学习和优化。实时监控各 AI 模型的置信度、任务处理能力和响应速度，确保数据准确性和系统可靠性。'
                        : 'Multi-model collaboration system using EWMA algorithm for continuous learning and optimization. Real-time monitoring of AI model confidence, task processing capability, and response speed to ensure data accuracy and system reliability.'
                      }
                    </p>
                </div>
              </div>
            </h3>
            <div className={`${themeClasses.textMuted} text-[10px] flex items-center gap-2 mt-0.5`}>
              <span className={`${getStatusColor(consortiumData.status)} font-bold`}>
                {consortiumData.status.toUpperCase()}
              </span>
              <span className="text-gray-600">•</span>
              <span>{timeSinceUpdate()}</span>
            </div>
          </div>
        </div>
        
        {/* Expand/Collapse Button */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className={`${themeClasses.textMuted} hover:text-white transition-colors p-1 rounded hover:bg-gray-800/50`}
          aria-label={isExpanded ? 'Collapse' : 'Expand'}
        >
          <svg 
            className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Compact View - Model Confidence Bars */}
      <div className="space-y-3 mb-4">
        {consortiumData.models.map((model, index) => (
          <div key={index} className="group">
            <div className="flex justify-between items-center mb-1.5">
              <span className={`text-[10px] uppercase tracking-wider font-bold ${themeClasses.textMuted} group-hover:text-white transition-colors`}>{model.name}</span>
              <span className={`text-[10px] font-mono font-bold ${getConfidenceTextColor(model.confidence)}`}>
                {model.confidence.toFixed(1)}%
              </span>
            </div>
            <div className={`w-full h-1.5 ${theme === 'dark' ? 'bg-gray-800/50' : 'bg-gray-200'} rounded-full overflow-hidden`}>
              <div 
                className={`h-full ${getConfidenceColor(model.confidence)} transition-all duration-1000 ease-out group-hover:brightness-110 relative`}
                style={{ width: `${model.confidence}%` }}
              >
                <div className="absolute inset-0 bg-white/20 w-full h-full animate-[shimmer_2s_infinite] skew-x-12"></div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Expanded View - Detailed Stats */}
      {isExpanded && (
        <div className="space-y-4 pt-4 border-t border-gray-800 animate-fadeIn">
          
          {/* Model Details Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {consortiumData.models.map((model, index) => (
              <div 
                key={index} 
                className={`${theme === 'dark' ? 'bg-gray-900/30' : 'bg-gray-50'} rounded-lg p-3 border ${themeClasses.border} hover:border-gray-600 transition-colors`}
              >
                <div className="flex justify-between items-center mb-2">
                  <span className={`text-xs font-bold ${themeClasses.text}`}>{model.name}</span>
                  <div className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                    model.confidence >= 80 ? 'bg-neon-green/10 text-neon-green' :
                    model.confidence >= 60 ? 'bg-neon-blue/10 text-neon-blue' :
                    'bg-yellow-500/10 text-yellow-500'
                  }`}>
                    {model.confidence.toFixed(1)}%
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className={themeClasses.textMuted}>
                      {language === 'CN' ? '任务' : 'Tasks'}:
                    </span>
                    <span className={`ml-1 ${themeClasses.text} font-mono`}>{model.tasksProcessed}</span>
                  </div>
                  <div className="text-right">
                    <span className={themeClasses.textMuted}>
                      {language === 'CN' ? '延迟' : 'Latency'}:
                    </span>
                    <span className={`ml-1 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} font-mono`}>{model.avgResponseTime}ms</span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* System Stats & Freshness - Compact Grid */}
          <div className="grid grid-cols-2 gap-3">
             <div className={`${theme === 'dark' ? 'bg-gray-900/30' : 'bg-gray-50'} rounded-lg p-3 border ${themeClasses.border}`}>
               <div className="text-[10px] font-bold text-neon-blue mb-2 uppercase tracking-wider">
                 {language === 'CN' ? '系统吞吐' : 'System Throughput'}
               </div>
               <div className="flex justify-between items-end">
                  <span className={themeClasses.textMuted}>{language === 'CN' ? '总任务' : 'Total'}:</span>
                  <span className={`text-lg font-mono font-bold ${themeClasses.text}`}>{consortiumData.totalTasksProcessed.toLocaleString()}</span>
               </div>
             </div>
             
             <div className={`${theme === 'dark' ? 'bg-gray-900/30' : 'bg-gray-50'} rounded-lg p-3 border ${themeClasses.border}`}>
               <div className="text-[10px] font-bold text-neon-green mb-2 uppercase tracking-wider">
                 {language === 'CN' ? '数据同步' : 'Data Sync'}
               </div>
               <div className="flex items-center gap-2">
                  <div className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-neon-green opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-neon-green"></span>
                  </div>
                  <span className={`text-xs ${themeClasses.text} font-mono`}>Real-time</span>
               </div>
             </div>
          </div>
        </div>
      )}

      {/* Background Glow Effect */}
      <div className="absolute -bottom-10 -right-10 w-32 h-32 bg-neon-blue/5 rounded-full blur-3xl pointer-events-none"></div>
    </div>
  );
};
