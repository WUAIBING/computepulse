import React from 'react';

interface LoadingSkeletonProps {
  language: 'EN' | 'CN';
}

export const LoadingSkeleton: React.FC<LoadingSkeletonProps> = ({ language }) => {
  const t = {
    EN: {
      loading: 'Loading real-time compute data...',
      fetching: 'Fetching latest GPU prices and token costs',
    },
    CN: {
      loading: '正在加载实时算力数据...',
      fetching: '获取最新GPU价格和代币成本',
    },
  }[language];

  return (
    <div className="min-h-[400px] flex flex-col items-center justify-center space-y-6">
      {/* Animated spinner */}
      <div className="relative">
        <div className="w-20 h-20 border-4 border-gray-800 rounded-full"></div>
        <div className="absolute top-0 left-0 w-20 h-20 border-4 border-t-neon-blue border-r-transparent border-b-transparent border-l-transparent rounded-full animate-spin"></div>
        <div className="absolute top-0 left-0 w-20 h-20 border-4 border-t-transparent border-r-neon-purple border-b-transparent border-l-transparent rounded-full animate-spin" style={{ animationDelay: '0.1s' }}></div>
      </div>

      {/* Loading text */}
      <div className="text-center space-y-2">
        <h3 className="text-xl font-bold text-white">{t.loading}</h3>
        <p className="text-gray-400 text-sm">{t.fetching}</p>
      </div>

      {/* Skeleton cards */}
      <div className="w-full max-w-4xl space-y-4 mt-8">
        <div className="bg-panel-bg/50 rounded-xl border border-gray-800 p-6">
          <div className="flex justify-between items-center mb-4">
            <div className="h-6 bg-gray-800 rounded w-1/4 animate-pulse"></div>
            <div className="h-4 bg-gray-800 rounded w-1/6 animate-pulse"></div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="bg-gray-900/50 rounded-lg p-4 space-y-3">
                <div className="h-4 bg-gray-800 rounded w-3/4 animate-pulse"></div>
                <div className="h-6 bg-gray-800 rounded w-1/2 animate-pulse"></div>
                <div className="h-3 bg-gray-800 rounded w-full animate-pulse"></div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-panel-bg/50 rounded-xl border border-gray-800 p-6">
          <div className="h-6 bg-gray-800 rounded w-1/3 mb-4 animate-pulse"></div>
          <div className="h-48 bg-gray-800 rounded w-full animate-pulse"></div>
        </div>
      </div>

      {/* Progress indicator */}
      <div className="w-64 space-y-2">
        <div className="flex justify-between text-xs text-gray-500">
          <span>0%</span>
          <span>50%</span>
          <span>100%</span>
        </div>
        <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-neon-blue to-neon-purple rounded-full animate-pulse"
            style={{ width: '75%' }}
          ></div>
        </div>
      </div>
    </div>
  );
};