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
  role: 'Architect' | 'Hunter' | 'Translator'; // Roles for the narrative
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

// --- Logo Components (SVG) ---
const QwenLogo = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 1024 1024" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Base Background Hexagon */}
    <path d="M512 0L955.5 256V768L512 1024L68.5 768V256L512 0Z" fill="#584BEB"/>
    
    {/* Inner White Structure - Abstract "Q" or Star shape based on the image */}
    <path d="M512 240L740 370V650L512 780L284 650V370L512 240Z" fill="white" fillOpacity="0.2"/>
    <path d="M512 300L680 400V620L512 720L344 620V400L512 300Z" fill="white"/>
    
    {/* Central Void/Core */}
    <path d="M512 420L590 465V555L512 600L434 555V465L512 420Z" fill="#584BEB"/>
  </svg>
);

const DeepSeekLogo = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 1024 1024" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
     {/* Simplified Whale Shape based on DeepSeek Logo */}
     <path d="M832 256c-20-30-60-40-100-20s-80 60-100 100c-20 40-40 80-60 120-20 40-60 60-100 60s-80-40-100-80c-20-40-20-100 20-140 20-20 60-20 100 0" stroke="#4D6BFE" strokeWidth="60" strokeLinecap="round" fill="none" opacity="0"/>
     
     {/* Body */}
     <path d="M512 128C300 128 128 300 128 512c0 212 172 384 384 384 212 0 384-172 384-384" fill="#4D6BFE" fillOpacity="0.9"/>
     
     {/* Tail */}
     <path d="M896 256c0 0-50 150-200 150S512 256 512 256" fill="#4D6BFE"/>
     
     {/* Eye */}
     <circle cx="650" cy="450" r="30" fill="white"/>
     
     {/* Belly / White Patch */}
     <path d="M300 550c0 0 100-100 250-50s200 200 200 200H300V550z" fill="white"/>
     
     {/* Redrawing a better approximation of the whale logo using path */}
     <path d="M256 450 C256 250, 450 150, 650 150 C750 150, 850 200, 880 250 C900 280, 850 320, 800 300 C750 280, 700 250, 750 200" fill="none" stroke="none"/> 
     
     {/* Actual Whale Path Approximation */}
     <path d="M192 512c0-176.7 143.3-320 320-320 80 0 150 30 210 80-40-20-80-20-110 10-40 40-20 100 40 140 40 25 100 25 140 0 50 60 80 140 80 220 0 120-60 220-160 280-40-20-80-60-100-100-20-40 0-100 40-140 20-20 60-30 90-20-30-50-80-90-140-110-60-20-120-10-170 30-60 50-90 120-80 190" fill="#4D6BFE"/>
     
     {/* Corrected Stylized Whale based on image provided */}
     <circle cx="512" cy="512" r="480" fill="none"/> {/* Bounds */}
     <path d="M250 400 C250 200, 500 100, 750 200 C850 240, 900 150, 850 100 M 750 200 C800 300, 950 300, 900 200" fill="none" stroke="none"/>

     {/* Final Vector Shape Construction */}
     <path d="M200 500 C200 300, 400 150, 650 180 C750 190, 820 150, 850 120 C840 180, 800 250, 700 280 C800 280, 900 250, 950 200 C920 300, 850 400, 750 450 C800 480, 850 550, 820 600 C700 750, 400 800, 300 700 C350 650, 500 600, 600 650 C550 550, 350 500, 200 500 Z" fill="#4D6BFE"/>
     <circle cx="620" cy="420" r="40" fill="white"/> 
  </svg>
);

const KimiLogo = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 1024 1024" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    {/* Base Circle - Dark Background */}
    <rect width="1024" height="1024" rx="256" fill="#121212"/>
    
    {/* K Shape */}
    <path d="M320 256V768H416V560L608 768H736L512 512L720 256H592L416 464V256H320Z" fill="white"/>
    
    {/* Blue Dot */}
    <circle cx="768" cy="256" r="64" fill="#2C68FF"/>
  </svg>
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
      ],
      lastUpdate: new Date().toISOString(),
      totalTasksProcessed: 5580,
      version: 'v1.2.4'
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
            
            {/* Agents Triangle Layout */}
            <div className="relative w-full max-w-xs h-64">
              {consortiumData.models.map((model, index) => {
                // Positioning: Triangle
                const positions = [
                  'top-0 left-1/2 -translate-x-1/2', // Top (Qwen)
                  'bottom-0 left-0',                 // Bottom Left (DeepSeek)
                  'bottom-0 right-0'                 // Bottom Right (Doubao)
                ];
                const isActive = logs.length > 0 && logs[logs.length - 1].agent === model.name;

                return (
                  <div key={model.name} className={`absolute ${positions[index]} flex flex-col items-center transition-all duration-500 ${isActive ? 'scale-110 z-10' : 'scale-100 opacity-70'}`}>
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
                       <div className={`absolute -top-2 px-2 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider bg-black border border-gray-700 text-white opacity-100 transition-opacity`}>
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
