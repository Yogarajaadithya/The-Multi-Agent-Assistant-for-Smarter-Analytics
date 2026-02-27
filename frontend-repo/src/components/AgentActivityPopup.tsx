import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useEffect, useRef, useState } from 'react';
import { XMarkIcon, CpuChipIcon, FunnelIcon, MagnifyingGlassIcon, ArrowDownTrayIcon, ChartBarIcon } from '@heroicons/react/24/outline';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  agent?: string;
  duration?: number; // Duration in milliseconds
  details?: string; // Additional error details or context
  stackTrace?: string; // Stack trace for errors
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  logs: LogEntry[];
  isProcessing: boolean;
}

export default function AgentActivityPopup({ isOpen, onClose, logs, isProcessing }: Props) {
  const logsEndRef = useRef<HTMLDivElement>(null);
  const [filterLevel, setFilterLevel] = useState<string>('all');
  const [filterAgent, setFilterAgent] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showStats, setShowStats] = useState(true);
  const [expandedErrors, setExpandedErrors] = useState<Set<number>>(new Set());
  const [groupByAgent, setGroupByAgent] = useState(false);
  const [showTimings, setShowTimings] = useState(true);

  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const getLogColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'info':
        return 'text-blue-400';
      case 'success':
        return 'text-green-400';
      case 'warning':
        return 'text-yellow-400';
      case 'error':
        return 'text-red-400';
      case 'debug':
        return 'text-purple-400';
      case 'critical':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  const getLogBgColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'bg-red-500/10 border-red-500/30';
      case 'warning':
        return 'bg-yellow-500/10 border-yellow-500/30';
      case 'success':
        return 'bg-green-500/10 border-green-500/30';
      case 'critical':
        return 'bg-red-600/20 border-red-600/50';
      default:
        return 'border-transparent';
    }
  };

  const getAgentIcon = (agent?: string) => {
    if (!agent) return '🤖';
    
    switch (agent.toLowerCase()) {
      case 'planner':
        return '🧭';
      case 'text-to-sql':
      case 'sql':
        return '💾';
      case 'visualization':
        return '📊';
      case 'hypothesis':
        return '🔬';
      case 'stats':
      case 'statistical':
        return '📈';
      default:
        return '⚡';
    }
  };

  // Filter and search logs
  const filteredLogs = logs.filter(log => {
    const matchesLevel = filterLevel === 'all' || log.level.toLowerCase() === filterLevel;
    const matchesAgent = filterAgent === 'all' || log.agent?.toLowerCase() === filterAgent.toLowerCase();
    const matchesSearch = searchQuery === '' || log.message.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLevel && matchesAgent && matchesSearch;
  });

  // Get unique agents and levels
  const uniqueAgents = Array.from(new Set(logs.filter(l => l.agent).map(l => l.agent)));
  const uniqueLevels = Array.from(new Set(logs.map(l => l.level.toLowerCase())));

  // Export logs function
  const exportLogs = () => {
    const logText = logs.map(log => 
      `[${log.timestamp}] [${log.level.toUpperCase()}] ${log.agent ? `[${log.agent}] ` : ''}${log.message}`
    ).join('\n');
    const blob = new Blob([logText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `agent-logs-${new Date().toISOString()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Calculate performance metrics
  const avgLogsPerAgent = uniqueAgents.length > 0 ? (logs.filter(l => l.agent).length / uniqueAgents.length).toFixed(1) : '0';
  const errorCount = logs.filter(l => l.level.toLowerCase() === 'error' || l.level.toLowerCase() === 'critical').length;
  const warningCount = logs.filter(l => l.level.toLowerCase() === 'warning').length;
  const successCount = logs.filter(l => l.level.toLowerCase() === 'success').length;
  
  // Better success rate: (agents with successes / total unique agents) * 100
  // This shows what % of agents completed successfully
  const agentsWithSuccess = new Set(
    logs.filter(l => l.agent && l.level.toLowerCase() === 'success').map(l => l.agent)
  ).size;
  const successRate = uniqueAgents.length > 0 ? ((agentsWithSuccess / uniqueAgents.length) * 100).toFixed(1) : '0';
  
  // Query success: Did we have any errors?
  const querySucceeded = errorCount === 0;
  const queryStatus = querySucceeded ? 'SUCCESS' : 'FAILED';
  
  // Calculate average duration per agent
  const agentDurations = logs
    .filter(l => l.agent && l.duration)
    .reduce((acc, log) => {
      if (!acc[log.agent!]) acc[log.agent!] = [];
      acc[log.agent!].push(log.duration!);
      return acc;
    }, {} as Record<string, number[]>);
  
  const avgAgentDuration = Object.entries(agentDurations).map(([agent, durations]) => ({
    agent,
    avgDuration: (durations.reduce((a, b) => a + b, 0) / durations.length / 1000).toFixed(2)
  }));

  // Get error logs with details
  const errorLogs = logs.filter(l => l.level.toLowerCase() === 'error' || l.level.toLowerCase() === 'critical');
  
  // Calculate total query time from all operations with duration
  let totalQueryTime = logs
    .filter(l => l.duration)
    .reduce((sum, log) => sum + (log.duration || 0), 0);
  
  // Fallback: If no duration data, calculate from first to last log timestamp
  if (totalQueryTime === 0 && logs.length > 1) {
    try {
      const parseTime = (timestamp: string) => {
        // Remove AM/PM and split
        const cleanTime = timestamp.replace(/\s*(AM|PM|am|pm)\s*$/i, '').trim();
        const parts = cleanTime.split(':');
        
        if (parts.length >= 3) {
          const hours = parseInt(parts[0], 10);
          const minutes = parseInt(parts[1], 10);
          const seconds = parseInt(parts[2], 10);
          return hours * 3600 + minutes * 60 + seconds;
        }
        return 0;
      };
      
      const firstTime = parseTime(logs[0].timestamp);
      const lastTime = parseTime(logs[logs.length - 1].timestamp);
      const diffSeconds = lastTime - firstTime;
      
      // Only use if we got a valid positive difference
      if (diffSeconds > 0) {
        totalQueryTime = diffSeconds * 1000; // Convert to milliseconds
      }
    } catch (e) {
      totalQueryTime = 0;
    }
  }
  
  const queryTimeSeconds = totalQueryTime > 0 ? (totalQueryTime / 1000).toFixed(2) : '--';
  
  // Toggle error expansion
  const toggleErrorExpansion = (index: number) => {
    const newExpanded = new Set(expandedErrors);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedErrors(newExpanded);
  };

  // Group logs by agent
  const groupedLogs = groupByAgent
    ? uniqueAgents.map(agent => ({
        agent,
        logs: filteredLogs.filter(l => l.agent === agent)
      }))
    : null;

  return (
    <Transition appear show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <Transition.Child
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" />
        </Transition.Child>

        <div className="fixed inset-0 overflow-y-auto">
          <div className="flex min-h-full items-center justify-center p-4">
            <Transition.Child
              as={Fragment}
              enter="ease-out duration-300"
              enterFrom="opacity-0 scale-95"
              enterTo="opacity-100 scale-100"
              leave="ease-in duration-200"
              leaveFrom="opacity-100 scale-100"
              leaveTo="opacity-0 scale-95"
            >
              <Dialog.Panel className="w-full max-w-3xl transform overflow-hidden rounded-3xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border-2 border-transparent bg-clip-padding shadow-2xl shadow-cyan-500/30 transition-all backdrop-blur-xl relative">
                {/* Animated border gradient */}
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-r from-cyan-500 via-blue-500 to-purple-500 opacity-40 animate-gradient-x" style={{padding: '2px', zIndex: -1}}></div>
                <div className="absolute inset-0 rounded-3xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 m-[2px]"></div>
                
                {/* Content wrapper */}
                <div className="relative z-10">
                {/* Header */}
                <div className="relative bg-gradient-to-r from-cyan-900/50 via-blue-900/50 to-purple-900/50 px-8 py-5 border-b-2 border-cyan-500/30">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="relative p-3 bg-gradient-to-br from-cyan-500/20 to-blue-500/20 rounded-xl border border-cyan-400/30">
                        <CpuChipIcon className="w-9 h-9 text-cyan-300" />
                        {isProcessing && (
                          <div className="absolute -top-1 -right-1 w-4 h-4 bg-green-500 rounded-full animate-pulse shadow-lg shadow-green-500/50">
                            <div className="absolute inset-0 bg-green-500 rounded-full animate-ping"></div>
                          </div>
                        )}
                      </div>
                      <div>
                        <Dialog.Title className="text-2xl font-bold bg-gradient-to-r from-cyan-300 via-blue-300 to-purple-300 bg-clip-text text-transparent tracking-tight">
                          Agent Activity Monitor
                        </Dialog.Title>
                        <p className="text-sm text-gray-300 mt-1 flex items-center gap-2">
                          {isProcessing ? (
                            <><span className="inline-block w-2 h-2 bg-green-400 rounded-full animate-pulse"></span> Processing your query...</>
                          ) : errorCount > 0 ? (
                            <><span className="inline-block w-2 h-2 bg-red-400 rounded-full"></span> Query completed with {errorCount} error{errorCount > 1 ? 's' : ''}</>
                          ) : (
                            <><span className="inline-block w-2 h-2 bg-green-400 rounded-full"></span> Query completed successfully</>
                          )}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setGroupByAgent(!groupByAgent)}
                        className={`p-2 rounded-lg transition-colors ${groupByAgent ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-gray-700/50 text-gray-400 hover:text-cyan-400'}`}
                        title="Group by agent"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                        </svg>
                      </button>
                      <button
                        onClick={() => setShowTimings(!showTimings)}
                        className={`p-2 rounded-lg transition-colors ${showTimings ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-gray-700/50 text-gray-400 hover:text-cyan-400'}`}
                        title="Toggle timings"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                      </button>
                      <button
                        onClick={() => setShowStats(!showStats)}
                        className={`p-2 rounded-lg transition-colors ${showStats ? 'bg-cyan-500/20 text-cyan-400' : 'hover:bg-gray-700/50 text-gray-400 hover:text-cyan-400'}`}
                        title="Toggle stats"
                      >
                        <ChartBarIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={exportLogs}
                        className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors text-gray-400 hover:text-cyan-400"
                        title="Export logs"
                      >
                        <ArrowDownTrayIcon className="w-5 h-5" />
                      </button>
                      <button
                        onClick={onClose}
                        className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors text-gray-400 hover:text-gray-200"
                      >
                        <XMarkIcon className="w-6 h-6" />
                      </button>
                    </div>
                  </div>
                  
                  {/* Filter and Search Controls */}
                  <div className="mt-4 flex flex-wrap gap-3">
                    <div className="relative flex-1 min-w-[200px]">
                      <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                      <input
                        type="text"
                        placeholder="Search logs..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500/50 transition-colors text-gray-200 placeholder-gray-500"
                      />
                    </div>
                    <select
                      value={filterLevel}
                      onChange={(e) => setFilterLevel(e.target.value)}
                      className="px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500/50 transition-colors text-gray-200 cursor-pointer"
                    >
                      <option value="all">All Levels</option>
                      {uniqueLevels.map(level => (
                        <option key={level} value={level}>{level.toUpperCase()}</option>
                      ))}
                    </select>
                    <select
                      value={filterAgent}
                      onChange={(e) => setFilterAgent(e.target.value)}
                      className="px-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg text-sm focus:outline-none focus:border-cyan-500/50 transition-colors text-gray-200 cursor-pointer"
                    >
                      <option value="all">All Agents</option>
                      {uniqueAgents.map(agent => (
                        <option key={agent} value={agent}>{agent}</option>
                      ))}
                    </select>
                    {(filterLevel !== 'all' || filterAgent !== 'all' || searchQuery) && (
                      <button
                        onClick={() => { setFilterLevel('all'); setFilterAgent('all'); setSearchQuery(''); }}
                        className="px-4 py-2 bg-red-500/20 hover:bg-red-500/30 border border-red-500/30 rounded-lg text-sm text-red-300 transition-colors"
                      >
                        Clear Filters
                      </button>
                    )}
                  </div>
                </div>

                {/* Logs Container */}
                <div className="p-8">
                  <div className="bg-black/60 rounded-2xl border-2 border-gray-700/50 overflow-hidden shadow-inner">
                    <div className="h-[28rem] overflow-y-auto p-5 space-y-1 font-mono text-sm custom-scrollbar">
                      {logs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                          <CpuChipIcon className="w-16 h-16 mb-3 opacity-30" />
                          <p className="text-sm">No activity yet</p>
                          <p className="text-xs mt-1">Send a query to see the magic happen!</p>
                        </div>
                      ) : filteredLogs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                          <FunnelIcon className="w-16 h-16 mb-3 opacity-30" />
                          <p className="text-sm">No logs match your filters</p>
                          <p className="text-xs mt-1">Try adjusting your search criteria</p>
                        </div>
                      ) : groupByAgent && groupedLogs ? (
                        // Grouped by agent view
                        groupedLogs.map(({ agent, logs: agentLogs }) => (
                          <div key={agent} className="mb-6">
                            <div className="sticky top-0 bg-gradient-to-r from-gray-800 to-gray-700 px-4 py-2 rounded-lg mb-3 border border-cyan-500/30 shadow-lg z-10">
                              <div className="flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                  <div className="text-2xl">{getAgentIcon(agent)}</div>
                                  <span className="text-cyan-300 font-bold text-lg">{agent}</span>
                                  <span className="text-gray-400 text-sm">({agentLogs.length} logs)</span>
                                </div>
                                <div className="flex items-center gap-2">
                                  {agentLogs.filter(l => l.level.toLowerCase() === 'error').length > 0 && (
                                    <span className="px-2 py-1 bg-red-500/20 text-red-400 rounded text-xs font-bold border border-red-500/30">
                                      {agentLogs.filter(l => l.level.toLowerCase() === 'error').length} errors
                                    </span>
                                  )}
                                  {agentLogs.filter(l => l.level.toLowerCase() === 'success').length > 0 && (
                                    <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded text-xs font-bold border border-green-500/30">
                                      {agentLogs.filter(l => l.level.toLowerCase() === 'success').length} success
                                    </span>
                                  )}
                                </div>
                              </div>
                            </div>
                            {agentLogs.map((log, idx) => (
                              <div key={idx} className="relative mb-2">
                                <div className={`flex items-start gap-4 p-3 pl-6 rounded-xl hover:bg-gradient-to-r hover:from-gray-800/40 hover:to-gray-800/20 transition-all duration-200 border ${getLogBgColor(log.level)} hover:border-cyan-500/20 group`}>
                                  <div className="flex-shrink-0 mt-1">
                                    <div className="w-8 h-8 flex items-center justify-center bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-lg border border-gray-600/30 text-lg group-hover:scale-110 group-hover:border-cyan-400/50 transition-all duration-200">
                                      {log.level.toLowerCase() === 'error' ? '❌' : log.level.toLowerCase() === 'warning' ? '⚠️' : log.level.toLowerCase() === 'success' ? '✅' : '📝'}
                                    </div>
                                  </div>
                                  <div className="flex-1 min-w-0">
                                    <div className="flex items-center gap-2 mb-2 flex-wrap">
                                      <span className="text-gray-400 text-xs font-medium">{log.timestamp}</span>
                                      <span className={`px-2 py-1 rounded-md text-xs font-bold ${getLogColor(log.level)} border border-current/20`}>
                                        {log.level.toUpperCase()}
                                      </span>
                                      {showTimings && log.duration && (
                                        <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs font-bold border border-purple-500/30">
                                          {(log.duration / 1000).toFixed(2)}s
                                        </span>
                                      )}
                                    </div>
                                    <p className="text-gray-200 leading-relaxed break-words text-sm">{log.message}</p>
                                    {log.details && (
                                      <div className="mt-2 p-2 bg-gray-900/50 rounded text-xs text-gray-400 border border-gray-700">
                                        {log.details}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        ))
                      ) : (
                        <>
                          {filteredLogs.map((log, index) => (
                            <div key={index} className="relative">
                              {/* Timeline indicator on the left */}
                              <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-cyan-500/50 to-purple-500/50"></div>
                              <div className="absolute left-[-3px] top-6 w-2 h-2 bg-cyan-400 rounded-full animate-pulse shadow-lg shadow-cyan-400/50"></div>
                              
                              <div className={`flex items-start gap-4 p-3 pl-6 rounded-xl hover:bg-gradient-to-r hover:from-gray-800/40 hover:to-gray-800/20 transition-all duration-200 animate-fadeIn border ${getLogBgColor(log.level)} hover:border-cyan-500/20 group`}>
                                <div className="flex-shrink-0 mt-1">
                                  <div className="w-10 h-10 flex items-center justify-center bg-gradient-to-br from-gray-700/50 to-gray-800/50 rounded-lg border border-gray-600/30 text-xl group-hover:scale-110 group-hover:border-cyan-400/50 transition-all duration-200 group-hover:shadow-lg group-hover:shadow-cyan-500/20">
                                    {getAgentIcon(log.agent)}
                                  </div>
                                </div>
                                <div className="flex-1 min-w-0">
                                  <div className="flex items-center gap-2 mb-2 flex-wrap">
                                    <span className="text-gray-400 text-xs font-medium flex items-center gap-1">
                                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                      </svg>
                                      {log.timestamp}
                                    </span>
                                    {log.agent && (
                                      <span className="relative overflow-hidden px-2 py-1 rounded-md text-xs font-bold bg-gradient-to-r from-cyan-500/20 to-blue-500/20 text-cyan-300 border border-cyan-500/30 shadow-sm group-hover:border-cyan-400/50 transition-all">
                                        <span className="relative z-10">{log.agent}</span>
                                        <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></span>
                                      </span>
                                    )}
                                    <span className={`px-2 py-1 rounded-md text-xs font-bold ${getLogColor(log.level)} border border-current/20 shadow-sm`}>
                                      {log.level.toUpperCase()}
                                    </span>
                                    {showTimings && log.duration && (
                                      <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded text-xs font-bold border border-purple-500/30">
                                        ⏱️ {(log.duration / 1000).toFixed(2)}s
                                      </span>
                                    )}
                                  </div>
                                  <div className="flex items-start justify-between gap-3">
                                    <div className="flex-1">
                                      <p className="text-gray-200 leading-relaxed break-words text-sm">
                                        {log.message}
                                      </p>
                                      {(log.level.toLowerCase() === 'error' || log.level.toLowerCase() === 'critical') && (log.details || log.stackTrace) && (
                                        <div className="mt-2">
                                          <button
                                            onClick={() => toggleErrorExpansion(index)}
                                            className="text-xs text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors"
                                          >
                                            {expandedErrors.has(index) ? (
                                              <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" /></svg> Hide Details</>
                                            ) : (
                                              <><svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg> Show Details</>
                                            )}
                                          </button>
                                          {expandedErrors.has(index) && (
                                            <div className="mt-2 p-3 bg-red-950/30 border border-red-500/30 rounded-lg">
                                              {log.details && (
                                                <div className="mb-2">
                                                  <div className="text-xs text-red-300 font-bold mb-1">Error Details:</div>
                                                  <div className="text-xs text-gray-300 font-mono bg-black/30 p-2 rounded">{log.details}</div>
                                                </div>
                                              )}
                                              {log.stackTrace && (
                                                <div>
                                                  <div className="text-xs text-red-300 font-bold mb-1">Stack Trace:</div>
                                                  <div className="text-xs text-gray-400 font-mono bg-black/30 p-2 rounded max-h-32 overflow-y-auto">
                                                    {log.stackTrace}
                                                  </div>
                                                </div>
                                              )}
                                            </div>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                    <button 
                                      onClick={() => navigator.clipboard.writeText(log.message)}
                                      className="opacity-0 group-hover:opacity-100 transition-opacity p-1.5 hover:bg-gray-700/50 rounded-md text-gray-400 hover:text-cyan-400"
                                      title="Copy message"
                                    >
                                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                                      </svg>
                                    </button>
                                  </div>
                                </div>
                              </div>
                              {/* Arrow connector between steps */}
                              {index < filteredLogs.length - 1 && (
                                <div className="flex items-center justify-center py-2 my-1">
                                  <div className="flex items-center gap-3 text-cyan-400/70">
                                    <div className="h-0.5 w-12 bg-gradient-to-r from-transparent via-cyan-400/50 to-cyan-400/60 rounded-full"></div>
                                    <div className="relative">
                                      <div className="absolute inset-0 bg-cyan-400/20 blur-md rounded-full"></div>
                                      <svg 
                                        className="w-5 h-5 animate-bounce-slow relative z-10" 
                                        fill="currentColor" 
                                        viewBox="0 0 24 24"
                                      >
                                        <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" transform="rotate(90 12 12)" />
                                      </svg>
                                    </div>
                                    <div className="h-0.5 w-12 bg-gradient-to-r from-cyan-400/60 via-cyan-400/50 to-transparent rounded-full"></div>
                                  </div>
                                </div>
                              )}
                            </div>
                          ))}
                          <div ref={logsEndRef} />
                        </>
                      )}
                    </div>
                  </div>

                  {/* Performance Metrics */}
                  {logs.length > 0 && showStats && (
                    <div className="mt-6 space-y-4">
                      {/* Quick Stats Bar */}
                      <div className="grid grid-cols-5 gap-3">
                        <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-3">
                          <div className="text-xs text-gray-400 mb-1">Avg/Agent</div>
                          <div className="text-xl font-bold text-cyan-400">{avgLogsPerAgent}</div>
                        </div>
                        <div className="bg-gray-800/40 border border-red-900/20 border-gray-700/50 rounded-lg p-3">
                          <div className="text-xs text-gray-400 mb-1">Errors</div>
                          <div className="text-xl font-bold text-red-400">{errorCount}</div>
                        </div>
                        <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-3">
                          <div className="text-xs text-gray-400 mb-1">Warnings</div>
                          <div className="text-xl font-bold text-yellow-400">{warningCount}</div>
                        </div>
                        <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-3">
                          <div className="text-xs text-gray-400 mb-1" title="% of agents that completed successfully">Agent Success</div>
                          <div className="text-xl font-bold text-green-400">{successRate}%</div>
                        </div>
                        <div className="bg-gray-800/40 border border-gray-700/50 rounded-lg p-3">
                          <div className="text-xs text-gray-400 mb-1" title="Total time to process query">Query Time</div>
                          <div className="text-xl font-bold text-purple-400">{queryTimeSeconds}s</div>
                        </div>
                      </div>
                      
                      {/* Agent Performance Timings */}
                      {avgAgentDuration.length > 0 && showTimings && (
                        <div className="mt-4">
                          <div className="text-sm font-bold text-gray-300 mb-2 flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                            Average Agent Duration
                          </div>
                          <div className="grid grid-cols-3 gap-2">
                            {avgAgentDuration.map(({ agent, avgDuration }) => (
                              <div key={agent} className="bg-gray-800/40 border border-purple-500/20 rounded-lg p-2">
                                <div className="text-xs text-gray-400 flex items-center gap-1">
                                  <span>{getAgentIcon(agent)}</span>
                                  <span>{agent}</span>
                                </div>
                                <div className="text-lg font-bold text-purple-400">{avgDuration}s</div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                      
                      {/* Error Summary Section */}
                      {errorLogs.length > 0 && (
                        <div className="mt-4">
                          <div className="text-sm font-bold text-red-400 mb-2 flex items-center gap-2">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            Recent Errors ({errorLogs.length})
                          </div>
                          <div className="space-y-2 max-h-40 overflow-y-auto">
                            {errorLogs.slice(0, 5).map((log, idx) => (
                              <div key={idx} className="bg-red-950/20 border border-red-500/30 rounded-lg p-2">
                                <div className="flex items-start gap-2">
                                  <span className="text-red-400 text-lg">❌</span>
                                  <div className="flex-1 min-w-0">
                                    <div className="text-xs text-gray-400">{log.timestamp}</div>
                                    <div className="text-xs text-red-300 font-medium mt-1">{log.agent || 'System'}</div>
                                    <div className="text-xs text-gray-300 mt-1 break-words">{log.message}</div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Stats Footer */}
                  {logs.length > 0 && showStats && (
                    <div className="mt-4 grid grid-cols-3 gap-4">
                      <div className="relative overflow-hidden bg-gradient-to-br from-blue-900/30 to-blue-800/20 border-2 border-blue-500/30 rounded-xl p-4 hover:border-blue-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-blue-500/20 hover:scale-105 cursor-pointer group">
                        <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-30 transition-opacity">
                          <svg className="w-8 h-8 text-blue-300" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M9 2a1 1 0 000 2h2a1 1 0 100-2H9z"></path>
                            <path fillRule="evenodd" d="M4 5a2 2 0 012-2 3 3 0 003 3h2a3 3 0 003-3 2 2 0 012 2v11a2 2 0 01-2 2H6a2 2 0 01-2-2V5zm3 4a1 1 0 000 2h.01a1 1 0 100-2H7zm3 0a1 1 0 000 2h3a1 1 0 100-2h-3zm-3 4a1 1 0 100 2h.01a1 1 0 100-2H7zm3 0a1 1 0 100 2h3a1 1 0 100-2h-3z" clipRule="evenodd"></path>
                          </svg>
                        </div>
                        <div className="text-xs text-blue-300 font-bold mb-2 tracking-wide flex items-center gap-1">
                          📋 TOTAL LOGS
                        </div>
                        <div className="text-3xl font-bold bg-gradient-to-br from-blue-300 to-blue-500 bg-clip-text text-transparent relative z-10">{logs.length}</div>
                      </div>
                      <div className="relative overflow-hidden bg-gradient-to-br from-green-900/30 to-green-800/20 border-2 border-green-500/30 rounded-xl p-4 hover:border-green-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-green-500/20 hover:scale-105 cursor-pointer group">
                        <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-30 transition-opacity">
                          <svg className="w-8 h-8 text-green-300" fill="currentColor" viewBox="0 0 24 24">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"></path>
                          </svg>
                        </div>
                        <div className="text-xs text-green-300 font-bold mb-2 tracking-wide flex items-center gap-1">
                          ✅ SUCCESS
                        </div>
                        <div className="text-3xl font-bold bg-gradient-to-br from-green-300 to-green-500 bg-clip-text text-transparent relative z-10">
                          {logs.filter(l => l.level.toLowerCase() === 'success').length}
                        </div>
                      </div>
                      <div className="relative overflow-hidden bg-gradient-to-br from-purple-900/30 to-purple-800/20 border-2 border-purple-500/30 rounded-xl p-4 hover:border-purple-400/50 transition-all duration-300 hover:shadow-lg hover:shadow-purple-500/20 hover:scale-105 cursor-pointer group">
                        <div className="absolute top-2 right-2 opacity-20 group-hover:opacity-30 transition-opacity">
                          <svg className="w-8 h-8 text-purple-300" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a5.972 5.972 0 00-.75-2.906A3.005 3.005 0 0119 15v3h-3zM4.75 12.094A5.973 5.973 0 004 15v3H1v-3a3 3 0 013.75-2.906z"></path>
                          </svg>
                        </div>
                        <div className="text-xs text-purple-300 font-bold mb-2 tracking-wide flex items-center gap-1" title="Includes System orchestrator + main agents">
                          🤖 AGENTS USED
                        </div>
                        <div className="text-3xl font-bold bg-gradient-to-br from-purple-300 to-purple-500 bg-clip-text text-transparent relative z-10">
                          {new Set(logs.filter(l => l.agent).map(l => l.agent)).size}
                        </div>
                        <div className="text-[10px] text-purple-400/60 mt-1">
                          {uniqueAgents.filter(a => a !== 'System').length} core + orchestrator
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
