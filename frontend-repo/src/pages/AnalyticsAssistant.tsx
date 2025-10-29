import { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, Bars3Icon, MagnifyingGlassIcon, TrashIcon } from '@heroicons/react/24/outline';
import Plot from 'react-plotly.js';
import CodeBlock from '../components/CodeBlock';
import { EXAMPLE_PROMPTS } from '../lib/api';
import { sendAnalyticsQuery } from '../api/client';

const STORAGE_KEY = 'analytics-history';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  text: string;
  ts: string;
  data?: any;
}

interface HistoryItem {
  id: string;
  prompt: string;
  ts: string;
}

export default function AnalyticsAssistant() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historySearch, setHistorySearch] = useState('');
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const [isDesktop, setIsDesktop] = useState(false);

  useEffect(() => {
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const updateBreakpoint = () => {
      setIsDesktop(window.innerWidth >= 1024);
    };

    updateBreakpoint();
    window.addEventListener('resize', updateBreakpoint);

    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  const saveHistory = (items: HistoryItem[]) => {
    setHistory(items);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const query = inputValue.trim();
    setInputValue('');
    setIsLoading(true);

    const newMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      text: query,
      ts: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);

    try {
      // Use the analytics query endpoint instead of general chat
      const response = await sendAnalyticsQuery(query);

      // Format the response message
      let responseText = '';
      
      if (response.message) {
        responseText = response.message;
      } else if (response.data && response.data.length > 0) {
        responseText = `Found ${response.data.length} result(s) for your query.`;
      } else {
        responseText = 'Query completed successfully!';
      }
      
      const assistantMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant' as const,
        text: responseText,
        ts: new Date().toISOString(),
        data: response // Store full response for rendering visualization and data
      };

      setMessages(prev => [...prev, assistantMessage]);

      const historyItem = {
        id: newMessage.id,
        prompt: query,
        ts: newMessage.ts
      };

      saveHistory([historyItem, ...history].slice(0, 10));
    } catch (error) {
      console.error('Analytics query failed:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          text: `Sorry, the query failed: ${errorMessage}. Please try rephrasing your question about the HR employee data.`,
          ts: new Date().toISOString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearHistory = () => {
    saveHistory([]);
    setMessages([]);
  };

  const loadHistoryItem = (item: HistoryItem) => {
    setInputValue(item.prompt);
    setSidebarOpen(false);
  };

  const filteredHistory = history.filter(item =>
    item.prompt.toLowerCase().includes(historySearch.toLowerCase())
  );

  const handleHistoryToggle = () => {
    if (isDesktop) {
      setSidebarVisible(prev => !prev);
    } else {
      setSidebarOpen(true);
    }
  };

  return (
    <div className="flex h-screen bg-background text-gray-100">
      {/* Sidebar for larger screens */}
      {sidebarVisible && (
        <aside className="hidden lg:flex lg:flex-col lg:w-80 lg:fixed lg:inset-y-0 bg-gray-900/50 border-r border-gray-800">
          <div className="flex flex-col flex-1 min-h-0 bg-gradient-to-b from-gray-900/50">
            <div className="flex items-center justify-between px-4 h-16 border-b border-gray-800">
              <h2 className="text-lg font-medium">History</h2>
              <button
                onClick={clearHistory}
                className="p-2 text-gray-400 hover:text-gray-300 transition-colors"
                title="Clear history"
              >
                <TrashIcon className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 flex flex-col min-h-0">
              <div className="px-4 py-2">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="search"
                    placeholder="Search history..."
                    value={historySearch}
                    onChange={e => setHistorySearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg 
                             text-sm focus:outline-none focus:border-gray-600 transition-colors"
                  />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto">
                {filteredHistory.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-gray-400">
                    No history items found
                  </div>
                ) : (
                  <div className="px-2 py-2 space-y-1">
                    {filteredHistory.map(item => (
                      <button
                        key={item.id}
                        onClick={() => loadHistoryItem(item)}
                        className="w-full px-2 py-2 text-left rounded-lg hover:bg-gray-800/50 transition-colors"
                      >
                        <div className="text-sm truncate">{item.prompt}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(item.ts).toLocaleString()}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </aside>
      )}

      {/* Mobile sidebar */}
      <Dialog as="div" open={sidebarOpen} onClose={setSidebarOpen} className="relative z-50 lg:hidden">
        <Dialog.Overlay className="fixed inset-0 bg-black/80" />
        <div className="fixed inset-0 flex">
          <Dialog.Panel className="relative flex flex-col w-full max-w-xs bg-gray-900">
            <div className="flex items-center justify-between px-4 h-16 border-b border-gray-800">
              <h2 className="text-lg font-medium">History</h2>
              <button onClick={() => setSidebarOpen(false)} className="p-2">
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>
            <div className="flex-1 flex flex-col min-h-0">
              <div className="px-4 py-2">
                <div className="relative">
                  <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="search"
                    placeholder="Search history..."
                    value={historySearch}
                    onChange={e => setHistorySearch(e.target.value)}
                    className="w-full pl-9 pr-4 py-2 bg-gray-800/50 border border-gray-700 rounded-lg 
                             text-sm focus:outline-none focus:border-gray-600 transition-colors"
                  />
                </div>
              </div>
              <div className="flex-1 overflow-y-auto">
                {filteredHistory.length === 0 ? (
                  <div className="px-4 py-8 text-center text-sm text-gray-400">
                    No history items found
                  </div>
                ) : (
                  <div className="px-2 py-2 space-y-1">
                    {filteredHistory.map(item => (
                      <button
                        key={item.id}
                        onClick={() => loadHistoryItem(item)}
                        className="w-full px-2 py-2 text-left rounded-lg hover:bg-gray-800/50 transition-colors"
                      >
                        <div className="text-sm truncate">{item.prompt}</div>
                        <div className="text-xs text-gray-500">
                          {new Date(item.ts).toLocaleString()}
                        </div>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>

  {/* Main content */}
  <main className={`flex-1 flex flex-col min-h-0 ${sidebarVisible ? 'lg:ml-80' : 'lg:ml-0'}`}>
        <header className="flex-none px-4 py-6 sm:px-6 lg:px-8 bg-gradient-to-b from-background/50">
          <div className="flex items-center gap-4 w-full max-w-6xl mx-auto">
            <button
              type="button"
              onClick={handleHistoryToggle}
              className="inline-flex items-center justify-center h-11 w-11 rounded-lg bg-gray-900/50 border border-gray-800 text-gray-300 hover:bg-gray-800/60 transition-colors"
              title="Toggle history"
              aria-pressed={isDesktop ? sidebarVisible : undefined}
            >
              {isDesktop && sidebarVisible ? (
                <XMarkIcon className="w-6 h-6" />
              ) : (
                <Bars3Icon className="w-6 h-6" />
              )}
              <span className="sr-only">Toggle history</span>
            </button>
            <div className="flex-1 text-center lg:text-left">
              <h1 className="text-3xl sm:text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Analytics Assistant
              </h1>
              <p className="mt-2 text-base sm:text-lg text-gray-400">
                Ask a question to the FastAPI-powered backend
              </p>
            </div>
          </div>
        </header>

        <div className="flex-1 min-h-0 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex flex-col min-h-0 w-full space-y-4">
            {/* Messages */}
            <div className="flex-1 min-h-0 overflow-y-auto space-y-4">
              {messages.length === 0 ? (
                <div className="flex items-center justify-center h-full text-gray-400">
                  Start the conversation to see responses here.
                </div>
              ) : (
                messages.map(message => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={`${message.role === 'user' ? 'max-w-[85%]' : 'max-w-[95%]'} rounded-2xl px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-500'
                          : 'bg-gray-800/50 border border-gray-700'
                      }`}
                    >
                      <div className="text-sm font-medium mb-1 opacity-75">
                        {message.role === 'user' ? 'You' : 'Assistant'}
                      </div>
                      <div className="whitespace-pre-wrap">{message.text}</div>

                      {message.role === 'assistant' && message.data?.sql && (
                        <div className="mt-4">
                          <div className="text-sm font-medium text-gray-400 mb-2">SQL Query</div>
                          <CodeBlock code={message.data.sql} language="sql" />
                        </div>
                      )}

                      {/* Render visualization if available */}
                      {message.role === 'assistant' && message.data?.visualization?.success && (
                        <div className="mt-4 bg-gray-900/50 rounded-lg p-4">
                          <Plot
                            data={message.data.visualization.plotly_json?.data ?? []}
                            layout={{
                              ...(message.data.visualization.plotly_json?.layout ?? {}),
                              autosize: true,
                              paper_bgcolor: 'rgba(0,0,0,0)',
                              plot_bgcolor: 'rgba(0,0,0,0)',
                              font: { color: '#e5e7eb', size: 11 },
                              margin: { l: 120, r: 80, t: 60, b: 100 },
                              height: 500,
                            }}
                            frames={message.data.visualization.plotly_json?.frames ?? []}
                            config={{ responsive: true, displayModeBar: true }}
                            style={{ width: '100%', height: '500px' }}
                          />
                        </div>
                      )}
                      {message.role === 'assistant' && message.data?.visualization && !message.data.visualization.success && (
                        <div className="mt-4 text-sm text-red-400">
                          Visualization error: {message.data.visualization.error}
                        </div>
                      )}
                      
                      {/* Show data table if available */}
                      {message.role === 'assistant' && message.data?.data && message.data.data.length > 0 && (
                        <div className="mt-4 overflow-x-auto">
                          <table className="min-w-full text-sm border-collapse">
                            <thead>
                              <tr className="border-b border-gray-700">
                                {Object.keys(message.data.data[0]).map(key => (
                                  <th key={key} className="px-3 py-2 text-left font-medium text-gray-400">
                                    {key}
                                  </th>
                                ))}
                              </tr>
                            </thead>
                            <tbody>
                              {message.data.data.slice(0, 10).map((row: any, i: number) => (
                                <tr key={i} className="border-b border-gray-800">
                                  {Object.values(row).map((value: any, j: number) => (
                                    <td key={j} className="px-3 py-2">
                                      {typeof value === 'number' ? value.toFixed(2) : value}
                                    </td>
                                  ))}
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          {message.data.data.length > 10 && (
                            <div className="text-xs text-gray-500 mt-2">
                              Showing 10 of {message.data.data.length} rows
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Agent Activity and Result Tabs removed */}

            {/* Input area */}
            <div className="flex-none bg-gray-900/50 rounded-xl p-4 border border-gray-800">
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="flex gap-4">
                  <input
                    type="text"
                    value={inputValue}
                    onChange={e => setInputValue(e.target.value)}
                    placeholder="Ask me about your analytics data..."
                    disabled={isLoading}
                    className="flex-1 bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-2
                             focus:outline-none focus:border-gray-600 transition-colors"
                  />
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="px-6 py-2 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-lg
                             font-medium disabled:opacity-50 disabled:cursor-not-allowed
                             hover:from-indigo-600 hover:to-purple-600 transition-all"
                  >
                    {isLoading ? 'Analyzing...' : 'Send'}
                  </button>
                </div>
                <div className="flex flex-wrap gap-2">
                  {EXAMPLE_PROMPTS.map((prompt, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setInputValue(prompt)}
                      className="px-3 py-1.5 text-sm bg-gray-800/50 hover:bg-gray-700/50 
                               rounded-full transition-colors"
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}