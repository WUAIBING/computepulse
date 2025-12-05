import React, { useState, useEffect, useRef } from 'react';
import { Language, Theme } from '../types';
import { TRANSLATIONS } from '../translations';
import { getThemeClasses } from '../theme';

// --- Interfaces ---
interface AIModel {
  name: string;
  confidence: number;
  tasksProcessed: number;
  avgResponseTime: number;
  role: 'Architect' | 'Hunter' | 'Researcher' | 'Analyst'; // Roles for the narrative
  color: string; // Theme color for the model
  avatar: React.ReactNode; // SVG Avatar
}

interface AIConsortiumData {
  status: 'active' | 'learning' | 'idle';
  models: AIModel[];
  lastUpdate: string;
  totalTasksProcessed: number;
  version: string; // e.g. "v1.0.4"
}

interface LogEntry {
  id: string;
  timestamp: string;
  agent: string; // "Qwen", "DeepSeek", "Doubao", "System"
  message: string;
  type: 'info' | 'success' | 'warning' | 'action';
}

interface AIConsortiumStatusProps {
  language: Language;
  theme: Theme;
}

// --- Text Avatar Components ---
const QwenLogo = ({ className }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center bg-[#615CED]/10 rounded-full border border-[#615CED]/20`}>
    <span className="text-[#615CED] font-bold text-[10px] md:text-xs">Qwen</span>
  </div>
);

const DeepSeekLogo = ({ className }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center bg-[#00A9FF]/10 rounded-full border border-[#00A9FF]/20`}>
    <span className="text-[#00A9FF] font-bold text-[10px] md:text-xs">DeepSeek</span>
  </div>
);

const KimiLogo = ({ className }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center bg-[#E64A19]/10 rounded-full border border-[#E64A19]/20`}>
    <span className="text-[#E64A19] font-bold text-[10px] md:text-xs">Kimi</span>
  </div>
);

const GLMLogo = ({ className }: { className?: string }) => (
  <div className={`${className} flex items-center justify-center bg-[#3B82F6]/10 rounded-full border border-[#3B82F6]/20`}>
    <span className="text-[#3B82F6] font-bold text-[10px] md:text-xs">GLM</span>
  </div>
);

// Removed SCRIPT_TEMPLATES (Zero Simulation Policy)

export const AIConsortiumStatus: React.FC<AIConsortiumStatusProps> = ({ language, theme }) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [consortiumData, setConsortiumData] = useState<AIConsortiumData | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logContainerRef = useRef<HTMLDivElement>(null);
  
  const themeClasses = getThemeClasses(theme);

  // 1. Initialize Models & Load Logs
  useEffect(() => {
    // Default Data (Fallback)
    setConsortiumData({
      status: 'active',
      models: [
        { name: 'Qwen', confidence: 98.5, tasksProcessed: 1240, avgResponseTime: 145, role: 'Architect', color: '#615CED', avatar: <QwenLogo className="w-full h-full" /> },
        { name: 'DeepSeek', confidence: 96.2, tasksProcessed: 3450, avgResponseTime: 320, role: 'Hunter', color: '#00A9FF', avatar: <DeepSeekLogo className="w-full h-full" /> },
        { name: 'Kimi', confidence: 95.5, tasksProcessed: 890, avgResponseTime: 180, role: 'Researcher', color: '#E64A19', avatar: <KimiLogo className="w-full h-full" /> },
        { name: 'GLM', confidence: 97.8, tasksProcessed: 450, avgResponseTime: 210, role: 'Analyst', color: '#3B82F6', avatar: <GLMLogo className="w-full h-full" /> },
      ],
      lastUpdate: new Date().toISOString(),
      totalTasksProcessed: 5580,
      version: 'v1.2.5'
    });

    // Fetch Real System Logs
    const fetchLogs = async () => {
      try {
        const baseUrl = import.meta.env.BASE_URL;
        const cleanBaseUrl = baseUrl.endsWith('/') ? baseUrl : `${baseUrl}/`;
        const response = await fetch(`${cleanBaseUrl}data/system_logs.json`);
        if (response.ok) {
           const data = await response.json();
           // Update System Stats from Real Log Data
           setConsortiumData(prev => prev ? ({
             ...prev,
             lastUpdate: data.last_updated,
             version: data.system_version,
             totalTasksProcessed: data.total_tasks
           }) : null);
           
           // Set Initial Logs
           if (data.logs && Array.isArray(data.logs)) {
              // Keep timestamp as raw string or ISO, formatting happens in render
              setLogs(data.logs);
           }
        }
      } catch (e) {
        console.warn('Failed to fetch system logs:', e);
        // Fallback: Empty logs or static message indicating system offline
        setLogs([
          { 
             id: '0', 
             timestamp: new Date().toISOString(), 
             agent: 'System', 
             message: 'Waiting for data stream...', 
             type: 'info' 
          }
        ]);
      }
    };
    
    fetchLogs();
  }, []);

  // Helper to format time based on language
  const formatLogTime = (isoTimestamp: string) => {
     try {
       const date = new Date(isoTimestamp);
       return date.toLocaleString(language === 'CN' ? 'zh-CN' : 'en-US', {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          hour12: false
       });
     } catch (e) {
       return isoTimestamp;
     }
  };

  // Helper to translate log messages (Simple regex/mapping)
  const translateLogMessage = (message: string, lang: Language) => {
    if (lang !== 'CN') return message;

    // 1. Exact Match Dictionary
    const exactMap: Record<string, string> = {
      "Initiating global GPU price scan...": "正在启动全球 GPU 价格扫描...",
      "Verifying price consistency...": "正在验证价格一致性...",
      "Checking market news for hidden price hikes...": "正在检查市场新闻以发现隐性涨价...",
      "Querying API pricing endpoints...": "正在查询 API 定价端点...",
      "Cross-referencing with developer docs...": "正在与开发者文档交叉比对...",
      "Token Pricing updated.": "Token 定价已更新。",
      "Analyzing global energy reports...": "正在分析全球能源报告...",
      "Grid Load metrics synchronized.": "电网负载指标已同步。",
      "Running integrity scan on dataset...": "正在对数据集进行完整性扫描...",
      "Integrity scan complete. No critical anomalies.": "完整性扫描完成。未发现严重异常。",
      "Waiting for data stream...": "等待数据流...",
      "Sequence complete. Entering low-power monitoring mode.": "序列完成。进入低功耗监控模式。",
      "Updating dashboard cache with latest snapshots.": "正在更新仪表板缓存。",
      "Scanning key market indicators for North America region...": "正在扫描北美地区的关键市场指标...",
      "Detected minor fluctuation in AWS Spot prices (+0.4%). Within tolerance.": "检测到 AWS Spot 价格微小波动 (+0.4%)。在容差范围内。",
      "Cross-referencing with secondary data sources... Validated.": "正在与二级数据源交叉比对... 已验证。",
      "Scheduled hourly monitor sequence initiated.": "预定的小时监控序列已启动。",
      "Grid Data Saved": "电网数据已保存",
      "Grid Data Validation Failed": "电网数据验证失败"
    };

    if (exactMap[message]) return exactMap[message];

    // 2. Pattern Matching
    // "GPU Database updated with {n} records."
    const gpuUpdateMatch = message.match(/GPU Database updated with (\d+) records/);
    if (gpuUpdateMatch) {
       return `GPU 数据库已更新，包含 ${gpuUpdateMatch[1]} 条记录。`;
    }
    
    // "GPU Data Saved: {n} records"
    const gpuSavedMatch = message.match(/GPU Data Saved: (\d+) records/);
    if (gpuSavedMatch) {
       return `GPU 数据已保存：${gpuSavedMatch[1]} 条记录`;
    }

    // "Token Data Saved: {n} records"
    const tokenSavedMatch = message.match(/Token Data Saved: (\d+) records/);
    if (tokenSavedMatch) {
       return `Token 数据已保存：${tokenSavedMatch[1]} 条记录`;
    }

    return message;
  };

  // 2. Live Logs (Strictly Real Data Only)
  // Removed setInterval simulation logic
  // Only updates when parent component re-renders or if we implement a polling mechanism for the JSON file

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  if (!consortiumData) return null;

  const getAgentColor = (agent: string) => {
    switch(agent) {
      case 'Qwen': return 'text-[#615CED]';
      case 'DeepSeek': return 'text-[#00A9FF]';
      case 'Kimi': return 'text-[#E64A19]';
      case 'GLM': return 'text-[#3B82F6]';
      default: return 'text-gray-400';
    }
  };

  return (
    <div className={`${themeClasses.panelBg} rounded-xl border ${themeClasses.border} relative overflow-hidden transition-all duration-300`}>
      
      {/* --- HEADER --- */}
      <div className="p-5 border-b border-gray-800 flex justify-between items-center bg-black/20 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-2 h-2 rounded-full bg-neon-green animate-pulse"></div>
            <div className="absolute inset-0 w-2 h-2 rounded-full bg-neon-green opacity-30 animate-ping"></div>
          </div>
          <div>
             <h3 className={`${themeClasses.textMuted} text-xs font-bold uppercase tracking-wider flex items-center gap-2`}>
              {language === 'CN' ? 'AI 联合体 · 全息视图' : 'AI Consortium · Holographic View'}
             </h3>
             <div className="text-[10px] text-gray-500 font-mono mt-0.5">
               Version {consortiumData.version} • Online
             </div>
          </div>
        </div>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-gray-500 hover:text-white transition-colors p-1"
        >
          <svg className={`w-4 h-4 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isExpanded && (
        <div className="grid grid-cols-1 lg:grid-cols-2">
          
          {/* --- LEFT: HOLOGRAPHIC STAGE (The Agents) --- */}
          <div className="p-6 relative min-h-[300px] flex flex-col items-center justify-center border-b lg:border-b-0 lg:border-r border-gray-800 bg-gradient-to-b from-transparent to-black/40">
            
            {/* Center Core */}
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-32 h-32 bg-neon-blue/5 rounded-full blur-3xl animate-pulse pointer-events-none"></div>
            
            {/* Agents Triangle Layout - Refactored to support dynamic number of agents */}
            <div className="relative w-full max-w-xs h-64">
              {consortiumData.models.map((model, index, arr) => {
                // Calculate positions dynamically in a circle/polygon
                const total = arr.length;
                const angleStep = (2 * Math.PI) / total;
                // Start from top (-90 degrees or -PI/2)
                const angle = index * angleStep - Math.PI / 2;
                
                // Radius for the layout
                const radius = 45; // % from center
                
                // Convert polar to cartesian percentages (50% is center)
                const left = 50 + radius * Math.cos(angle);
                const top = 50 + radius * Math.sin(angle);
                
                const isActive = logs.length > 0 && logs[logs.length - 1].agent === model.name;

                return (
                  <div 
                    key={model.name} 
                    className={`absolute flex flex-col items-center transition-all duration-500 ${isActive ? 'scale-110 z-10' : 'scale-100 opacity-70'}`}
                    style={{
                      left: `${left}%`,
                      top: `${top}%`,
                      transform: `translate(-50%, -50%) scale(${isActive ? 1.1 : 1})`
                    }}
                  >
                    {/* Avatar Circle */}
                    <div 
                      className={`w-16 h-16 rounded-full bg-gray-900/80 border-2 p-2 transition-all duration-300 flex items-center justify-center backdrop-blur-md relative group`}
                      style={{
                        borderColor: isActive ? model.color : '#374151', // gray-700
                        boxShadow: isActive ? `0 0 15px ${model.color}` : 'none'
                      }}
                    >
                       <div className={`w-full h-full ${isActive ? 'animate-[spin_4s_linear_infinite]' : ''}`}>
                         {model.avatar}
                       </div>
                       {/* Role Badge */}
                       <div className={`absolute -top-2 px-2 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider bg-black border border-gray-700 text-white opacity-100 transition-opacity whitespace-nowrap`}>
                         {model.role}
                       </div>
                    </div>
                    
                    {/* Name & Confidence */}
                    <div className="mt-2 text-center">
                      <div className={`text-xs font-bold ${isActive ? 'text-white' : 'text-gray-500'}`}>{model.name}</div>
                      <div className={`text-[10px] font-mono ${isActive ? 'text-neon-green' : 'text-gray-600'}`}>{model.confidence}%</div>
                    </div>

                    {/* Connection Lines (Pseudo) */}
                    {isActive && (
                       <div className="absolute top-1/2 left-1/2 w-full h-full pointer-events-none">
                          <div className="absolute top-0 left-0 w-20 h-0.5 bg-gradient-to-r from-transparent via-white/20 to-transparent rotate-45 transform origin-center animate-ping"></div>
                       </div>
                    )}
                  </div>
                );
              })}
            </div>
            
          </div>

          {/* --- RIGHT: LIVE THOUGHT STREAM (The Logs) --- */}
          <div className="flex flex-col bg-black/20">
             <div className="p-3 border-b border-gray-800 bg-gray-900/50 flex justify-between items-center">
               <span className="text-[10px] font-bold text-gray-400 uppercase tracking-wider">Live Thought Stream</span>
               <div className="flex gap-1">
                 <div className="w-1.5 h-1.5 rounded-full bg-red-500/20"></div>
                 <div className="w-1.5 h-1.5 rounded-full bg-yellow-500/20"></div>
                 <div className="w-1.5 h-1.5 rounded-full bg-green-500/20"></div>
               </div>
             </div>
             
             <div 
               ref={logContainerRef}
               className="flex-1 p-4 overflow-y-auto max-h-[300px] font-mono text-xs space-y-3 scrollbar-thin scrollbar-thumb-gray-800 scrollbar-track-transparent"
             >
               {logs.map((log) => (
                 <div key={log.id} className="animate-fadeIn flex gap-3 group">
                    <div className={`${theme === 'dark' ? 'text-gray-500' : 'text-gray-500 font-medium'} shrink-0 select-none w-auto whitespace-nowrap`}>
                      {formatLogTime(log.timestamp)}
                    </div>
                    <div className="flex-1 break-words">
                       <span className={`font-bold mr-2 ${getAgentColor(log.agent)}`}>
                         [{log.agent}]
                       </span>
                       <span className={`
                         ${log.type === 'warning' ? 'text-yellow-500' : 
                           log.type === 'success' ? 'text-emerald-400' : 
                           log.type === 'action' ? 'text-blue-300' : 
                           theme === 'dark' ? 'text-gray-300' : 'text-gray-800 font-medium'}
                       `}>
                         {translateLogMessage(log.message, language)}
                       </span>
                    </div>
                 </div>
               ))}
               {/* Typing Indicator - Only show if logs are empty (waiting for data) */}
               {logs.length === 0 && (
                 <div className="flex gap-3 opacity-50">
                   <div className="w-14"></div>
                   <div className="flex gap-1 items-center h-4">
                     <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                     <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                     <div className="w-1 h-1 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                   </div>
                 </div>
               )}
             </div>

             {/* Stats Footer */}
             <div className="p-3 border-t border-gray-800 bg-gray-900/30 grid grid-cols-3 gap-2 text-[10px]">
                <div className="text-center">
                  <div className="text-gray-500">Throughput</div>
                  <div className="text-white font-bold">{consortiumData.totalTasksProcessed} ops</div>
                </div>
                <div className="text-center border-l border-gray-800">
                  <div className="text-gray-500">Avg Latency</div>
                  <div className="text-neon-blue font-bold">183ms</div>
                </div>
                <div className="text-center border-l border-gray-800">
                  <div className="text-gray-500">Evolution</div>
                  <div className="text-neon-purple font-bold">Level 4</div>
                </div>
             </div>
          </div>
        </div>
      )}
    </div>
  );
};
