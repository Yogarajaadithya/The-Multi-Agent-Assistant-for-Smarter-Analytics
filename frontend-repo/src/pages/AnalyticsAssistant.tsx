import { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, Bars3Icon, MagnifyingGlassIcon, TrashIcon } from '@heroicons/react/24/outline';
import AgentActivity from '../components/AgentActivity';
import Tabs from '../components/Tabs';
import CodeBlock from '../components/CodeBlock';
import { analyze, AnalyzeResponse, EXAMPLE_PROMPTS, HistoryItem, Message } from '../lib/api';

const STORAGE_KEY = 'analytics-history';

export default function AnalyticsAssistant() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [historySearch, setHistorySearch] = useState('');
  const [currentResponse, setCurrentResponse] = useState<AnalyzeResponse | null>(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
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

    const newMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      text: query,
      ts: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);

    try {
      const response = await analyze(query);
      setCurrentResponse(response);

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        text: response.insights?.text || 'Analysis complete.',
        ts: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

      const historyItem: HistoryItem = {
        id: newMessage.id,
        prompt: query,
        ts: newMessage.ts
      };

      saveHistory([historyItem, ...history].slice(0, 10));
    } catch (error) {
      console.error('Analysis failed:', error);
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          text: 'Sorry, the analysis failed. Please try again.',
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
    setCurrentResponse(null);
  };

  const loadHistoryItem = (item: HistoryItem) => {
    setInputValue(item.prompt);
    setSidebarOpen(false);
  };

  const filteredHistory = history.filter(item =>
    item.prompt.toLowerCase().includes(historySearch.toLowerCase())
  );

  const renderTabContent = () => {
    if (!currentResponse) return null;

    return [
      {
        label: 'EDA',
        content: currentResponse.eda && (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(currentResponse.eda.summary).map(([key, value]) => (
                <div key={key} className="bg-gray-800/50 rounded-lg p-4">
                  <div className="text-sm text-gray-400">{key.replace(/_/g, ' ')}</div>
                  <div className="text-lg font-semibold">{value}</div>
                </div>
              ))}
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-800">
                <thead>
                  <tr>
                    {Object.keys(currentResponse.eda.preview[0] || {}).map(key => (
                      <th key={key} className="px-4 py-2 text-left text-sm font-medium text-gray-400">
                        {key}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {currentResponse.eda.preview.map((row, i) => (
                    <tr key={i}>
                      {Object.values(row).map((value, j) => (
                        <td key={j} className="px-4 py-2 text-sm">
                          {value}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )
      },
      {
        label: 'Stats',
        content: currentResponse.stats && (
          <div className="space-y-4">
            <div className="bg-gray-800/50 rounded-lg p-4">
              <h3 className="font-medium mb-2">{currentResponse.stats.test}</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div>
                  <div className="text-sm text-gray-400">Statistic</div>
                  <div className="font-mono">{currentResponse.stats.statistic.toFixed(3)}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-400">p-value</div>
                  <div className="font-mono">{currentResponse.stats.p_value.toFixed(4)}</div>
                </div>
                {currentResponse.stats.effect_size && (
                  <div>
                    <div className="text-sm text-gray-400">Effect size</div>
                    <div className="font-mono">{currentResponse.stats.effect_size.toFixed(2)}</div>
                  </div>
                )}
              </div>
              {currentResponse.stats.note && (
                <div className="mt-2 text-sm text-gray-400">{currentResponse.stats.note}</div>
              )}
            </div>
          </div>
        )
      },
      {
        label: 'Visualization',
        content: currentResponse.viz && (
          <div className="aspect-video bg-gray-800/50 rounded-lg p-4">
            <div id="chart-root" className="w-full h-full" />
          </div>
        )
      },
      {
        label: 'SQL / Audit',
        content: currentResponse.audit && (
          <div className="space-y-4">
            {currentResponse.audit.sql && (
              <CodeBlock code={currentResponse.audit.sql} language="sql" />
            )}
            {currentResponse.audit.steps && (
              <div className="bg-gray-800/50 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-400 mb-2">Steps</h3>
                <ol className="list-decimal list-inside space-y-1">
                  {currentResponse.audit.steps.map((step, i) => (
                    <li key={i} className="text-sm">{step}</li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        )
      },
      {
        label: 'Insights',
        content: currentResponse.insights && (
          <div className="space-y-4">
            <p className="text-gray-300">{currentResponse.insights.text}</p>
            <div>
              <h3 className="text-sm font-medium text-gray-400 mb-2">Suggested questions</h3>
              <div className="flex flex-wrap gap-2">
                {currentResponse.insights.suggestions.map((suggestion, i) => (
                  <button
                    key={i}
                    onClick={() => setInputValue(suggestion)}
                    className="px-3 py-1.5 text-sm bg-gray-800/50 hover:bg-gray-700/50 
                             rounded-full transition-colors"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )
      }
    ];
  };

  return (
    <div className="flex h-screen bg-background text-gray-100">
      {/* Sidebar for larger screens */}
      <div className="hidden lg:flex lg:flex-col lg:w-80 lg:fixed lg:inset-y-0 bg-gray-900/50 border-r border-gray-800">
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
      </div>

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
            <div className="flex-1 overflow-y-auto">
              {/* Same history content as desktop */}
            </div>
          </Dialog.Panel>
        </div>
      </Dialog>

      {/* Main content */}
      <main className="lg:pl-80 flex-1 flex flex-col min-h-0">
        <header className="flex-none px-4 py-8 sm:px-6 lg:px-8 bg-gradient-to-b from-background/50">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              Analytics Assistant
            </h1>
            <p className="mt-2 text-lg text-gray-400">
              Ask a question to the FastAPI-powered backend
            </p>
          </div>
        </header>

        <div className="flex-1 min-h-0 px-4 py-4 sm:px-6 lg:px-8">
          <div className="max-w-4xl mx-auto flex flex-col min-h-0">
            {/* Messages */}
            <div className="flex-1 min-h-0 overflow-y-auto space-y-4 mb-4">
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
                      className={`max-w-[85%] rounded-2xl px-4 py-2 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-indigo-500 to-purple-500'
                          : 'bg-gray-800/50 border border-gray-700'
                      }`}
                    >
                      <div className="text-sm font-medium mb-1 opacity-75">
                        {message.role === 'user' ? 'You' : 'Assistant'}
                      </div>
                      <div>{message.text}</div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Agent Activity */}
            {currentResponse && (
              <div className="mb-4">
                <AgentActivity activity={currentResponse.activity} />
              </div>
            )}

            {/* Result Tabs */}
            {currentResponse && (
              <div className="mb-4 bg-gray-900/50 rounded-xl p-4 border border-gray-800">
                <Tabs tabs={renderTabContent().filter(tab => tab.content)} />
              </div>
            )}

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