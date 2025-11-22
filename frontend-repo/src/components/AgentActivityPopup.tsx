import { Dialog, Transition } from '@headlessui/react';
import { Fragment, useEffect, useRef } from 'react';
import { XMarkIcon, CpuChipIcon } from '@heroicons/react/24/outline';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  agent?: string;
}

interface Props {
  isOpen: boolean;
  onClose: () => void;
  logs: LogEntry[];
  isProcessing: boolean;
}

export default function AgentActivityPopup({ isOpen, onClose, logs, isProcessing }: Props) {
  const logsEndRef = useRef<HTMLDivElement>(null);

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
      default:
        return 'text-gray-400';
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
              <Dialog.Panel className="w-full max-w-2xl transform overflow-hidden rounded-2xl bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 border border-cyan-500/30 shadow-2xl shadow-cyan-500/20 transition-all">
                {/* Header */}
                <div className="relative bg-gradient-to-r from-cyan-900/40 via-blue-900/40 to-purple-900/40 px-6 py-4 border-b border-cyan-500/20">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="relative">
                        <CpuChipIcon className="w-8 h-8 text-cyan-400" />
                        {isProcessing && (
                          <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse">
                            <div className="absolute inset-0 bg-green-500 rounded-full animate-ping"></div>
                          </div>
                        )}
                      </div>
                      <div>
                        <Dialog.Title className="text-xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                          Agent Activity Monitor
                        </Dialog.Title>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {isProcessing ? '🔄 Processing your query...' : '✓ Ready for next query'}
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={onClose}
                      className="p-2 rounded-lg hover:bg-gray-700/50 transition-colors text-gray-400 hover:text-gray-200"
                    >
                      <XMarkIcon className="w-6 h-6" />
                    </button>
                  </div>
                </div>

                {/* Logs Container */}
                <div className="p-6">
                  <div className="bg-black/40 rounded-lg border border-gray-700/50 overflow-hidden">
                    <div className="h-96 overflow-y-auto p-4 space-y-2 font-mono text-xs">
                      {logs.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                          <CpuChipIcon className="w-16 h-16 mb-3 opacity-30" />
                          <p className="text-sm">No activity yet</p>
                          <p className="text-xs mt-1">Send a query to see the magic happen!</p>
                        </div>
                      ) : (
                        <>
                          {logs.map((log, index) => (
                            <div
                              key={index}
                              className="flex items-start gap-3 p-2 rounded hover:bg-gray-800/30 transition-colors animate-fadeIn"
                            >
                              <span className="text-lg flex-shrink-0 mt-0.5">
                                {getAgentIcon(log.agent)}
                              </span>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-gray-500 text-[10px]">
                                    {log.timestamp}
                                  </span>
                                  {log.agent && (
                                    <span className="px-1.5 py-0.5 rounded text-[9px] font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                                      {log.agent}
                                    </span>
                                  )}
                                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${getLogColor(log.level)}`}>
                                    {log.level.toUpperCase()}
                                  </span>
                                </div>
                                <p className="text-gray-300 leading-relaxed break-words">
                                  {log.message}
                                </p>
                              </div>
                            </div>
                          ))}
                          <div ref={logsEndRef} />
                        </>
                      )}
                    </div>
                  </div>

                  {/* Stats Footer */}
                  {logs.length > 0 && (
                    <div className="mt-4 grid grid-cols-3 gap-3">
                      <div className="bg-gradient-to-br from-blue-900/20 to-blue-800/10 border border-blue-500/20 rounded-lg p-3">
                        <div className="text-[10px] text-blue-300 font-semibold mb-1">TOTAL LOGS</div>
                        <div className="text-2xl font-bold text-blue-400">{logs.length}</div>
                      </div>
                      <div className="bg-gradient-to-br from-green-900/20 to-green-800/10 border border-green-500/20 rounded-lg p-3">
                        <div className="text-[10px] text-green-300 font-semibold mb-1">SUCCESS</div>
                        <div className="text-2xl font-bold text-green-400">
                          {logs.filter(l => l.level.toLowerCase() === 'success').length}
                        </div>
                      </div>
                      <div className="bg-gradient-to-br from-purple-900/20 to-purple-800/10 border border-purple-500/20 rounded-lg p-3">
                        <div className="text-[10px] text-purple-300 font-semibold mb-1">AGENTS USED</div>
                        <div className="text-2xl font-bold text-purple-400">
                          {new Set(logs.filter(l => l.agent).map(l => l.agent)).size}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </div>
      </Dialog>
    </Transition>
  );
}
