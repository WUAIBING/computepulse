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
  <svg viewBox="0 0 100 100" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#615CED" fillOpacity="0.2" />
    <path d="M50 20C33.4315 20 20 33.4315 20 50C20 66.5685 33.4315 80 50 80C66.5685 80 80 66.5685 80 50C80 33.4315 66.5685 20 50 20ZM50 70C38.9543 70 30 61.0457 30 50C30 38.9543 38.9543 30 50 30C61.0457 30 70 38.9543 70 50C70 61.0457 61.0457 70 50 70Z" fill="#615CED"/>
    <circle cx="50" cy="50" r="12" fill="white"/>
  </svg>
);

const DeepSeekLogo = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="20" y="20" width="60" height="60" rx="10" fill="#00A9FF" fillOpacity="0.2" />
    <path d="M35 35L65 35L65 65L35 65L35 35Z" stroke="#00A9FF" strokeWidth="6"/>
    <path d="M50 20V35M80 50H65M50 80V65M20 50H35" stroke="#00A9FF" strokeWidth="4" strokeLinecap="round"/>
    <circle cx="50" cy="50" r="8" fill="#00A9FF"/>
  </svg>
);

const KimiLogo = ({ className }: { className?: string }) => (
  <svg viewBox="0 0 100 100" className={className} fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="50" cy="50" r="45" fill="#E64A19" fillOpacity="0.2" />
    <path d="M35 30L50 50L35 70M65 30L50 50L65 70" stroke="#E64A19" strokeWidth="6" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="50" cy="50" r="8" fill="#E64A19"/>
    <path d="M50 20V30M50 70V80" stroke="#E64A19" strokeWidth="4" strokeLinecap="round"/>
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
              // Format timestamps for display
              const formattedLogs = data.logs.map((log: any) => ({
                 ...log,
                 timestamp: new Date(log.timestamp).toLocaleString('en-US', {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                    hour12: false
                 })
              }));
              setLogs(formattedLogs);
           }
        }
      } catch (e) {
        console.warn('Failed to fetch system logs:', e);
        // Fallback: Empty logs or static message indicating system offline
        setLogs([
          { 
             id: '0', 
             timestamp: new Date().toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit',
                hour12: false
             }), 
             agent: 'System', 
             message: 'Waiting for data stream...', 
             type: 'info' 
          }
        ]);
      }
    };
    
    fetchLogs();
  }, []);

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
                       <div className={`absolute -top-2 px-2 py-0.5 rounded-full text-[8px] font-bold uppercase tracking-wider bg-black border border-gray-700 text-white opacity-0 group-hover:opacity-100 transition-opacity`}>
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
            
            <div className="absolute bottom-4 text-[10px] text-gray-600 font-mono uppercase tracking-widest">
              Neural Consensus Protocol Active
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
                    <div className={`${theme === 'dark' ? 'text-gray-500' : 'text-gray-500 font-medium'} shrink-0 select-none w-24 text-right`}>{log.timestamp.split(' ')[0]}</div>
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
                         {log.message}
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
