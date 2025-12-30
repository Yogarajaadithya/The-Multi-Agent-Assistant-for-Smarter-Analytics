import { useState, useEffect } from 'react';
import { Dialog } from '@headlessui/react';
import { XMarkIcon, Bars3Icon, MagnifyingGlassIcon, TrashIcon } from '@heroicons/react/24/outline';
import Plot from 'react-plotly.js';
import CodeBlock from '../components/CodeBlock';
import Tabs from '../components/Tabs';
import AgentActivityPopup from '../components/AgentActivityPopup';
import { getExamplePrompts } from '../lib/api';
import { sendAnalyticsQuery, getDatasets, switchDataset, getCurrentDataset } from '../api/client';

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

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  agent?: string;
}

interface Dataset {
  id: string;
  name: string;
  description: string;
  schema_name: string;
  main_table: string;
  is_active: boolean;
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
  const [activityPopupOpen, setActivityPopupOpen] = useState(false);
  const [agentLogs, setAgentLogs] = useState<LogEntry[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [currentDataset, setCurrentDataset] = useState<Dataset | null>(null);
  const [examplePrompts, setExamplePrompts] = useState<string[]>([]);
  const [datasetMenuOpen, setDatasetMenuOpen] = useState(false);
  const [showDatasetBanner, setShowDatasetBanner] = useState(false);
  const [bannerMessage, setBannerMessage] = useState('');

  useEffect(() => {
    const savedHistory = localStorage.getItem(STORAGE_KEY);
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
    
    // Load datasets and current dataset
    loadDatasets();
  }, []);

  const loadDatasets = async () => {
    try {
      const [datasetsResponse, currentResponse] = await Promise.all([
        getDatasets(),
        getCurrentDataset()
      ]);
      
      if (datasetsResponse.success) {
        setDatasets(datasetsResponse.datasets);
      }
      
      if (currentResponse.success) {
        setCurrentDataset(currentResponse.dataset);
        setExamplePrompts(getExamplePrompts(currentResponse.dataset.id));
      }
    } catch (error) {
      console.error('Failed to load datasets:', error);
    }
  };

  useEffect(() => {
    if (typeof window === 'undefined') return;

    const updateBreakpoint = () => {
      setIsDesktop(window.innerWidth >= 1024);
    };

    updateBreakpoint();
    window.addEventListener('resize', updateBreakpoint);

    return () => window.removeEventListener('resize', updateBreakpoint);
  }, []);

  useEffect(() => {
    // Close dataset menu when clicking outside
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (datasetMenuOpen && !target.closest('.dataset-menu-container')) {
        setDatasetMenuOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [datasetMenuOpen]);

  const saveHistory = (items: HistoryItem[]) => {
    setHistory(items);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
  };

  const addLog = (message: string, level: string = 'info', agent?: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setAgentLogs(prev => [...prev, { timestamp, level, message, agent }]);
  };

  const handleDatasetSwitch = async (datasetId: string) => {
    if (isLoading) return;
    
    try {
      setDatasetMenuOpen(false);
      
      const response = await switchDataset(datasetId);
      
      if (response.success) {
        setCurrentDataset(response.dataset);
        setExamplePrompts(getExamplePrompts(response.dataset.id));
        
        // Update datasets list to reflect active state
        setDatasets(prev => prev.map(ds => ({
          ...ds,
          is_active: ds.id === datasetId
        })));
        
        // Show banner notification
        setBannerMessage(`Dataset switched to "${response.dataset.name}" - ${response.dataset.description}`);
        setShowDatasetBanner(true);
        
        // Auto-hide banner after 4 seconds
        setTimeout(() => {
          setShowDatasetBanner(false);
        }, 4000);
      }
    } catch (error) {
      console.error('Failed to switch dataset:', error);
      addLog('Failed to switch dataset', 'error', 'System');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const query = inputValue.trim();
    setInputValue('');
    setIsLoading(true);
    setAgentLogs([]); // Clear previous logs

    const newMessage = {
      id: Date.now().toString(),
      role: 'user' as const,
      text: query,
      ts: new Date().toISOString()
    };

    setMessages(prev => [...prev, newMessage]);
    addLog(`Received query: "${query}"`, 'info', 'System');

    try {
      // Use the multi-agent system endpoint (routes through Planner Agent)
      addLog('Sending query to multi-agent system...', 'info', 'System');
      addLog('Routing through Planner Agent...', 'info', 'Planner');
      console.log('🔵 Calling sendAnalyticsQuery with question:', query);
      const response = await sendAnalyticsQuery(query);
      addLog('Received response from backend', 'success', 'System');
      
      // Debug: Log the full response
      console.log('🟢 Full response received:', response);
      console.log('🟢 Response keys:', Object.keys(response));
      console.log('🟢 Question type:', response.question_type);
      console.log('🟢 Has data?', !!response.data);
      console.log('🟢 Data length:', response.data?.length);
      console.log('🟢 Success?:', response.success);

      // Format the response message based on question type
      let responseText = '';
      
      // Check for errors first
      if (response.error || response.success === false) {
        addLog(`Query failed: ${response.error || 'Unknown error'}`, 'error', 'System');
        responseText = `Query failed: ${response.error || 'Unknown error occurred'}\n\nPlease try rephrasing your question or check the data.`;
      } else if (response.question_type === 'WHAT') {
        addLog('Question classified as WHAT (Descriptive Analytics)', 'info', 'Planner');
        addLog('Activating Text-to-SQL Agent...', 'info', 'Text-to-SQL');
        addLog('Generating SQL query from natural language...', 'info', 'Text-to-SQL');
        if (response.sql) {
          addLog('SQL query generated successfully', 'success', 'Text-to-SQL');
        }
        addLog('Activating Visualization Agent...', 'info', 'Visualization');
        if (response.visualization?.success) {
          addLog('Visualization created successfully', 'success', 'Visualization');
        }
        // Descriptive analytics response (SQL + Visualization)
        if (response.message) {
          responseText = response.message;
        } else if (response.data && response.data.length > 0) {
          responseText = `Found ${response.data.length} result(s) for your query.\n\nQuestion Type: WHAT (Descriptive Analytics)\nAgents Used: Text-to-SQL + Visualization`;
        } else {
          responseText = 'Query completed successfully!\n\nQuestion Type: WHAT (Descriptive Analytics)';
        }
      } else if (response.question_type === 'WHY') {
        addLog('Question classified as WHY (Causal Analytics)', 'info', 'Planner');
        // Causal analytics response (Hypothesis + Statistical Testing + Visualizations)
        const numHypotheses = response.hypotheses?.hypotheses?.length || 0;
        const numTests = response.statistical_results?.hypothesis_results?.length || 0;
        const numVisualizations = response.visualizations?.length || 0;
        
        addLog('Activating Hypothesis Generation Agent...', 'info', 'Hypothesis');
        if (numHypotheses > 0) {
          addLog(`Generated ${numHypotheses} hypotheses`, 'success', 'Hypothesis');
          addLog('Activating Text-to-SQL Agent for hypothesis testing...', 'info', 'Text-to-SQL');
          addLog(`Generated ${numHypotheses} SQL queries`, 'success', 'Text-to-SQL');
          addLog('Activating Visualization Agent...', 'info', 'Visualization');
          addLog(`Created ${numVisualizations} visualizations`, 'success', 'Visualization');
          addLog('Activating Statistical Testing Agent...', 'info', 'Stats');
          addLog(`Completed ${numTests} statistical tests`, 'success', 'Stats');
        } else {
          addLog('Hypothesis generation failed', 'error', 'Hypothesis');
        }
        
        responseText = `Generated ${numHypotheses} hypotheses with ${numVisualizations} visualizations and conducted ${numTests} statistical test(s).\n\nQuestion Type: WHY (Causal Analytics)\nAgents Used: Hypothesis Generation + Text-to-SQL + Visualization + Statistical Testing`;
        
        // Add summary of significant findings
        if (response.statistical_results?.hypothesis_results) {
          const significantResults = response.statistical_results.hypothesis_results.filter(
            (result: any) => result.statistical_results?.p_value < 0.05
          );
          
          if (significantResults.length > 0) {
            responseText += `\n\nSignificant Findings: ${significantResults.length} out of ${numTests} hypotheses showed statistically significant results (p < 0.05)`;
          }
        }
      } else {
        responseText = response.message || 'Analysis completed successfully!';
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
      addLog('Query processing completed successfully', 'success', 'System');
    } catch (error) {
      console.error('[ERROR] Analytics query failed:', error);
      console.error('[ERROR] Error type:', typeof error);
      console.error('[ERROR] Error details:', error);
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      addLog(`Fatal error: ${errorMessage}`, 'error', 'System');
      setMessages(prev => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          role: 'assistant' as const,
          text: `Sorry, the query failed: ${errorMessage}.\n\nTips:\n- For WHAT questions (facts, counts, distributions): Ask about metrics and comparisons\n- For WHY questions (causes, relationships): Ask about reasons and correlations\n- Make sure your question relates to the ${currentDataset?.name || 'current'} dataset.`,
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
    <div className="flex h-screen bg-background text-gray-100 overflow-x-hidden max-w-full">
      {/* Dataset Switch Banner */}
      {showDatasetBanner && (
        <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 animate-slide-down">
          <div className="bg-gradient-to-r from-cyan-500/90 to-blue-500/90 backdrop-blur-sm px-6 py-3 rounded-lg shadow-2xl border border-cyan-400/30 flex items-center gap-3 max-w-2xl">
            <svg className="w-5 h-5 text-white flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-white text-sm font-medium">{bannerMessage}</p>
            <button 
              onClick={() => setShowDatasetBanner(false)}
              className="ml-2 text-white/80 hover:text-white transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      )}
      
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
  <main className={`flex-1 flex flex-col h-screen overflow-hidden ${sidebarVisible ? 'lg:ml-80' : 'lg:ml-0'}`}>
        <header className="flex-none px-4 py-4 sm:px-6 lg:px-8 bg-gradient-to-r from-gray-900/80 via-cyan-900/20 to-blue-900/20 backdrop-blur-sm border-b border-gray-800/50">
          <div className="flex items-center gap-4 w-full max-w-6xl">
            <button
              type="button"
              onClick={handleHistoryToggle}
              className="inline-flex items-center justify-center h-11 w-11 rounded-xl bg-gradient-to-br from-cyan-500/10 to-blue-500/10 border border-cyan-500/20 text-cyan-300 hover:from-cyan-500/20 hover:to-blue-500/20 hover:border-cyan-400/40 transition-all duration-200 shadow-lg shadow-cyan-500/10"
              title="Toggle history"
              aria-pressed={isDesktop ? sidebarVisible : undefined}
            >
              {isDesktop && sidebarVisible ? (
                <XMarkIcon className="w-5 h-5" />
              ) : (
                <Bars3Icon className="w-5 h-5" />
              )}
              <span className="sr-only">Toggle history</span>
            </button>
            
            {/* Dataset Switcher */}
            <div className="relative dataset-menu-container">
              <button
                onClick={() => setDatasetMenuOpen(!datasetMenuOpen)}
                disabled={isLoading}
                className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-br from-purple-500/10 to-pink-500/10 border border-purple-500/30 text-purple-200 hover:from-purple-500/20 hover:to-pink-500/20 hover:border-purple-400/40 transition-all duration-200 shadow-lg shadow-purple-500/10 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Switch Dataset"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
                <span className="text-sm font-medium hidden sm:inline">
                  {currentDataset ? currentDataset.name : 'Select Dataset'}
                </span>
                <svg className={`w-4 h-4 transition-transform ${datasetMenuOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                </svg>
              </button>
              
              {/* Dropdown Menu */}
              {datasetMenuOpen && (
                <div className="absolute top-full left-0 mt-2 w-72 bg-gray-900 border border-purple-500/30 rounded-xl shadow-2xl shadow-purple-500/20 z-50 overflow-hidden">
                  <div className="p-2 bg-gradient-to-r from-purple-500/10 to-pink-500/10 border-b border-purple-500/20">
                    <p className="text-xs font-semibold text-purple-200">Available Datasets</p>
                  </div>
                  <div className="max-h-64 overflow-y-auto">
                    {datasets.map(dataset => (
                      <button
                        key={dataset.id}
                        onClick={() => handleDatasetSwitch(dataset.id)}
                        disabled={dataset.is_active || isLoading}
                        className={`w-full px-4 py-3 text-left transition-all duration-200 ${
                          dataset.is_active
                            ? 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 border-l-4 border-purple-500'
                            : 'hover:bg-purple-500/10 border-l-4 border-transparent hover:border-purple-500/50'
                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`text-sm font-medium ${dataset.is_active ? 'text-purple-200' : 'text-gray-200'}`}>
                                {dataset.name}
                              </span>
                              {dataset.is_active && (
                                <span className="px-2 py-0.5 text-xs font-semibold bg-gradient-to-r from-green-500/20 to-emerald-500/20 text-green-300 rounded-full border border-green-500/30">
                                  Active
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-400 mt-1">{dataset.description}</p>
                            <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                              <span>Table: {dataset.main_table}</span>
                            </div>
                          </div>
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex-1 text-center">
                <div className="inline-flex items-center gap-3 px-6 py-2 rounded-full bg-gradient-to-r from-cyan-500/10 via-blue-500/10 to-teal-500/10 border border-cyan-500/20 shadow-lg shadow-cyan-500/20">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-gradient-to-r from-emerald-400 to-green-500 animate-pulse shadow-lg shadow-emerald-500/50"></div>
                  <span className="text-xs font-medium text-gray-400">Online</span>
                </div>
                <div className="h-4 w-px bg-gray-700"></div>
                <h1 className="text-xl sm:text-2xl font-bold bg-gradient-to-r from-cyan-400 via-blue-400 to-teal-400 bg-clip-text text-transparent">
                  Analytics Assistant
                </h1>
              </div>
            </div>
          </div>
        </header>

        <div className="flex-1 min-h-0 px-4 pb-3 sm:px-6 lg:px-8 overflow-hidden flex flex-col">
          <div className="flex flex-col h-full w-full max-w-full mx-auto gap-3">
            {/* Messages - scrollable area */}
            <div className="flex-1 min-h-0 overflow-y-auto space-y-3 max-w-full pr-2">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full">
                  <div className="relative mb-8">
                    <div className="absolute inset-0 bg-gradient-to-r from-indigo-500 to-purple-500 blur-3xl opacity-20 rounded-full"></div>
                    <svg className="w-24 h-24 relative text-indigo-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                    </svg>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-300 mb-2">Ready to Analyze</h3>
                  <p className="text-gray-500 text-center max-w-md">Ask questions about your data and get instant insights with AI-powered analytics</p>
                </div>
              ) : (
                messages.map(message => (
                  <div
                    key={message.id}
                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} max-w-full animate-fadeIn`}
                  >
                    <div
                      className={`${message.role === 'user' ? 'max-w-[85%]' : 'max-w-[95%]'} w-full rounded-2xl px-4 py-3 ${
                        message.role === 'user'
                          ? 'bg-gradient-to-r from-cyan-500 via-blue-500 to-teal-500 shadow-lg shadow-cyan-500/30'
                          : 'bg-gradient-to-br from-gray-800/60 to-gray-900/60 border border-gray-700/50 shadow-xl shadow-cyan-500/5 backdrop-blur-sm'
                      }`}
                      style={{ maxWidth: '100%', overflow: 'hidden' }}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-2 h-2 rounded-full ${message.role === 'user' ? 'bg-white/80' : 'bg-cyan-400/80'}`}></div>
                        <div className="text-xs font-semibold opacity-90">
                          {message.role === 'user' ? 'You' : 'Analytics Assistant'}
                        </div>
                        <div className="text-[10px] text-gray-400 ml-auto">
                          {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                      </div>
                      <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.text}</div>

                      {/* Tabbed interface for assistant responses */}
                      {message.role === 'assistant' && message.data && (
                        <div className="mt-4">
                          <Tabs
                            tabs={[
                              {
                                label: 'Response',
                                content: (
                                  <div className="space-y-3">
                                    {/* For WHY questions - Show summary */}
                                    {message.data.question_type === 'WHY' && message.data.summary && (
                                      <>
                                        {message.data.summary.total_hypotheses === 0 ? (
                                          <div className="bg-red-900/20 rounded-lg p-4 border border-red-500/30">
                                            <div className="text-sm font-medium text-red-300 mb-2">Hypothesis Generation Failed</div>
                                            <div className="text-xs text-gray-300">
                                              {message.data.error || 'No hypotheses were generated. This could be due to:'}
                                            </div>
                                            <ul className="text-xs text-gray-400 mt-2 ml-4 list-disc space-y-1">
                                              <li>LM Studio might not be running</li>
                                              <li>The model might be overloaded</li>
                                              <li>The question might need to be rephrased</li>
                                            </ul>
                                            <div className="mt-3 text-xs text-gray-300">
                                              Try: Make sure LM Studio is running on port 1234, or try asking a different WHY question.
                                            </div>
                                          </div>
                                        ) : (
                                          <div className="bg-gradient-to-br from-purple-900/20 to-indigo-900/20 rounded-lg p-4 border border-purple-500/30">
                                            <div className="text-sm font-medium text-purple-300 mb-3">Causal Analysis Summary</div>
                                            <div className="space-y-2 text-xs">
                                              <div className="flex items-center gap-2">
                                                <span className="text-gray-400">Total Hypotheses Generated:</span>
                                                <span className="text-white font-semibold">{message.data.summary.total_hypotheses}</span>
                                              </div>
                                              <div className="flex items-center gap-2">
                                                <span className="text-gray-400">Visualizations Created:</span>
                                                <span className="text-white font-semibold">{message.data.summary.visualizations_generated || 0}</span>
                                              </div>
                                              <div className="flex items-center gap-2">
                                                <span className="text-gray-400">Statistical Tests Completed:</span>
                                                <span className="text-white font-semibold">{message.data.summary.tests_completed}</span>
                                              </div>
                                              {message.data.statistical_results?.hypothesis_results && (
                                                <div className="flex items-center gap-2">
                                                  <span className="text-gray-400">Significant Results:</span>
                                                  <span className="text-green-400 font-semibold">
                                                    {message.data.statistical_results.hypothesis_results.filter(
                                                      (r: any) => r.statistical_results?.p_value < 0.05
                                                    ).length} out of {message.data.statistical_results.hypothesis_results.length}
                                                  </span>
                                                </div>
                                              )}
                                            </div>
                                            <div className="mt-4 pt-3 border-t border-purple-500/20 text-xs text-gray-300">
                                              <span className="text-purple-200">Scroll below to view all hypothesis visualizations. Check the Stats tab for detailed testing results.</span>
                                            </div>
                                          </div>
                                        )}
                                      </>
                                    )}
                                    
                                    {/* Multiple Visualizations for WHY questions */}
                                    {message.data.question_type === 'WHY' && message.data.visualizations && message.data.visualizations.length > 0 && (
                                      <div className="space-y-4 mt-4">
                                        {message.data.visualizations.map((viz: any, idx: number) => (
                                          <div key={idx} className="bg-gray-900/50 rounded-lg p-3 border border-purple-500/20">
                                            <div className="text-sm font-medium text-purple-300 mb-2">
                                              Hypothesis {idx + 1} Visualization
                                            </div>
                                            {message.data.hypotheses?.hypotheses?.[idx] && (
                                              <div className="text-xs text-gray-400 mb-3 italic">
                                                {message.data.hypotheses.hypotheses[idx].null_hypothesis}
                                              </div>
                                            )}
                                            {viz.success ? (
                                              <div className="w-full" style={{ maxWidth: '100%', overflow: 'hidden' }}>
                                                <Plot
                                                  data={viz.plotly_json?.data ?? []}
                                                  layout={{
                                                    ...(viz.plotly_json?.layout ?? {}),
                                                    autosize: true,
                                                    paper_bgcolor: 'rgba(0,0,0,0)',
                                                    plot_bgcolor: 'rgba(0,0,0,0)',
                                                    font: { color: '#e5e7eb', size: 10 },
                                                    margin: { l: 100, r: 30, t: 40, b: 80 },
                                                    height: 350,
                                                  }}
                                                  frames={viz.plotly_json?.frames ?? []}
                                                  config={{ responsive: true, displayModeBar: true }}
                                                  style={{ width: '100%', maxWidth: '100%' }}
                                                  useResizeHandler={true}
                                                />
                                              </div>
                                            ) : (
                                              <div className="text-xs text-red-400">
                                                Visualization error: {viz.error || 'Unknown error'}
                                              </div>
                                            )}
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {/* Single Visualization for WHAT questions */}
                                    {message.data.question_type === 'WHAT' && message.data.visualization?.success && (
                                      <div className="bg-gray-900/50 rounded-lg p-3 max-w-full overflow-hidden">
                                        <div className="w-full" style={{ maxWidth: '100%', overflow: 'hidden' }}>
                                          <Plot
                                            data={message.data.visualization.plotly_json?.data ?? []}
                                            layout={{
                                              ...(message.data.visualization.plotly_json?.layout ?? {}),
                                              autosize: true,
                                              paper_bgcolor: 'rgba(0,0,0,0)',
                                              plot_bgcolor: 'rgba(0,0,0,0)',
                                              font: { color: '#e5e7eb', size: 10 },
                                              margin: { l: 100, r: 30, t: 40, b: 80 },
                                              height: 350,
                                            }}
                                            frames={message.data.visualization.plotly_json?.frames ?? []}
                                            config={{ responsive: true, displayModeBar: true }}
                                            style={{ width: '100%', maxWidth: '100%' }}
                                            useResizeHandler={true}
                                          />
                                        </div>
                                      </div>
                                    )}
                                    {message.data.question_type === 'WHAT' && message.data.visualization && !message.data.visualization.success && (
                                      <div className="text-xs text-red-400">
                                        Visualization error: {message.data.visualization.error}
                                      </div>
                                    )}
                                    
                                    {/* Data Table for WHAT questions */}
                                    {message.data.data && message.data.data.length > 0 && (
                                      <div className="w-full" style={{ maxWidth: '100%', overflow: 'hidden' }}>
                                        <div className="overflow-x-auto">
                                          <table className="min-w-full text-xs border-collapse">
                                            <thead>
                                              <tr className="border-b border-gray-700">
                                                {Object.keys(message.data.data[0]).map(key => (
                                                  <th key={key} className="px-2 py-1.5 text-left font-medium text-gray-400 whitespace-nowrap text-xs">
                                                    {key}
                                                  </th>
                                                ))}
                                              </tr>
                                            </thead>
                                            <tbody>
                                              {message.data.data.slice(0, 10).map((row: any, i: number) => (
                                                <tr key={i} className="border-b border-gray-800">
                                                  {Object.values(row).map((value: any, j: number) => (
                                                    <td key={j} className="px-2 py-1.5 whitespace-nowrap text-xs">
                                                      {typeof value === 'number' ? value.toFixed(2) : value}
                                                    </td>
                                                  ))}
                                                </tr>
                                              ))}
                                            </tbody>
                                          </table>
                                        </div>
                                        {message.data.data.length > 10 && (
                                          <div className="text-xs text-gray-500 mt-1.5">
                                            Showing 10 of {message.data.data.length} rows
                                          </div>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                ),
                              },
                              {
                                label: 'Code',
                                content: (
                                  <div className="space-y-4">
                                    {/* Multiple SQL Queries for WHY questions */}
                                    {message.data.question_type === 'WHY' && message.data.sql_queries && message.data.sql_queries.length > 0 && (
                                      <div className="space-y-4">
                                        {message.data.sql_queries.map((sql: string, idx: number) => (
                                          <div key={idx}>
                                            <div className="text-sm font-medium text-purple-300 mb-2">
                                              Hypothesis {idx + 1} SQL Query
                                            </div>
                                            {message.data.hypotheses?.hypotheses?.[idx] && (
                                              <div className="text-xs text-gray-400 mb-2 italic">
                                                {message.data.hypotheses.hypotheses[idx].null_hypothesis}
                                              </div>
                                            )}
                                            <CodeBlock code={sql} language="sql" />
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                    
                                    {/* Multiple Visualization Codes for WHY questions */}
                                    {message.data.question_type === 'WHY' && message.data.visualizations && message.data.visualizations.length > 0 && (
                                      <div className="space-y-4">
                                        {message.data.visualizations.map((viz: any, idx: number) => (
                                          viz.code && (
                                            <div key={idx}>
                                              <div className="text-sm font-medium text-purple-300 mb-2">
                                                Hypothesis {idx + 1} Visualization Code
                                              </div>
                                              <CodeBlock code={viz.code} language="python" />
                                            </div>
                                          )
                                        ))}
                                      </div>
                                    )}
                                    
                                    {/* Single SQL Query for WHAT questions */}
                                    {message.data.question_type === 'WHAT' && message.data.sql && (
                                      <div>
                                        <div className="text-sm font-medium text-gray-300 mb-2">Data Filter SQL</div>
                                        <CodeBlock code={message.data.sql} language="sql" />
                                      </div>
                                    )}
                                    
                                    {/* Single Visualization Code for WHAT questions */}
                                    {message.data.question_type === 'WHAT' && message.data.visualization?.code && (
                                      <div>
                                        <div className="text-sm font-medium text-gray-300 mb-2">Visualization Python</div>
                                        <CodeBlock code={message.data.visualization.code} language="python" />
                                      </div>
                                    )}
                                    
                                    {!message.data.sql && !message.data.sql_queries && !message.data.visualization?.code && !message.data.visualizations?.some((v: any) => v.code) && (
                                      <div className="text-xs text-gray-500">No code available</div>
                                    )}
                                  </div>
                                ),
                              },
                              {
                                label: 'Stats',
                                content: message.data.question_type === 'WHY' ? (
                                  message.data.statistical_results?.error ? (
                                    <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4">
                                      <div className="text-sm font-medium text-red-400 mb-2">Statistical Testing Error</div>
                                      <div className="text-xs text-red-300">{message.data.statistical_results.error}</div>
                                    </div>
                                  ) : message.data.statistical_results?.hypothesis_results && message.data.statistical_results.hypothesis_results.length > 0 ? (
                                  <div className="bg-gray-900/30 rounded-lg p-4">
                                    <div className="text-sm font-medium text-gray-300 mb-3">Stats Summary</div>
                                    <div className="space-y-4 text-xs text-gray-400 font-mono">
                                      {message.data.statistical_results.hypothesis_results.map((result: any, idx: number) => {
                                        const stats = result.statistical_results;
                                        const isSignificant = stats?.p_value < 0.05;
                                        
                                        return (
                                          <div key={idx} className="border-l-2 border-gray-700 pl-3">
                                            <div className="text-gray-300 mb-2">
                                              === Statistical Test Reasoning and Results ===
                                            </div>
                                            
                                            {/* Hypothesis */}
                                            {message.data.hypotheses?.hypotheses?.[idx] && (
                                              <div className="mb-2">
                                                <div>Hypothesis: {message.data.hypotheses.hypotheses[idx].null_hypothesis}</div>
                                              </div>
                                            )}
                                            
                                            {/* Test Results */}
                                            {stats && (
                                              <>
                                                <div>Test: {stats.test_name}</div>
                                                <div>p-value: {typeof stats.p_value === 'number' ? stats.p_value.toFixed(4) : stats.p_value}</div>
                                                
                                                {/* Test-specific statistics */}
                                                {stats.chi2_statistic !== undefined && (
                                                  <div>Chi-square: χ² = {stats.chi2_statistic.toFixed(3)}, Cramér's V = {stats.cramers_v?.toFixed(3)}</div>
                                                )}
                                                {stats.t_statistic !== undefined && (
                                                  <div>T-test: t = {stats.t_statistic.toFixed(3)}, Cohen's d = {stats.cohens_d?.toFixed(3)}</div>
                                                )}
                                                {stats.f_statistic !== undefined && (
                                                  <div>ANOVA: F = {stats.f_statistic.toFixed(3)}, η² = {stats.eta_squared?.toFixed(3)}</div>
                                                )}
                                                {stats.correlation !== undefined && (
                                                  <div>Correlation: r = {stats.correlation.toFixed(3)}, R² = {stats.r_squared?.toFixed(3)}</div>
                                                )}
                                                
                                                <div className="mt-2">
                                                  Is the hypothesis significant? {isSignificant ? 'True' : 'False'}
                                                </div>
                                                
                                                {/* Interpretation */}
                                                {stats.interpretation && (
                                                  <div className="mt-2 text-gray-300">
                                                    Conclusion: {stats.interpretation}
                                                  </div>
                                                )}
                                              </>
                                            )}
                                          </div>
                                        );
                                      })}
                                    </div>
                                  </div>
                                  ) : (
                                    <div className="bg-gray-900/30 rounded-lg p-4">
                                      <div className="text-sm text-gray-400">No statistical test results available.</div>
                                    </div>
                                  )
                                ) : (
                                  <div className="p-4">
                                    {message.data.question_type === 'WHAT' && message.data.data && message.data.data.length > 0 ? (
                                      <div className="bg-gray-900/30 rounded-lg p-4">
                                        <div className="text-sm font-medium text-gray-300 mb-3">Data Statistics Summary</div>
                                        <div className="space-y-3 text-xs text-gray-400">
                                          {/* Dataset Overview */}
                                          <div className="border-l-2 border-gray-700 pl-3">
                                            <div className="text-gray-300 mb-2">Dataset Overview</div>
                                            <div>Total Rows: {message.data.data.length}</div>
                                            <div>Total Columns: {Object.keys(message.data.data[0]).length}</div>
                                            <div className="mt-1">
                                              Columns: {Object.keys(message.data.data[0]).join(', ')}
                                            </div>
                                          </div>
                                          
                                          {/* Numeric Column Statistics */}
                                          {Object.keys(message.data.data[0]).map(key => {
                                            const values = message.data.data.map((row: any) => row[key]).filter((v: any) => typeof v === 'number');
                                            if (values.length === 0) return null;
                                            
                                            const sum = values.reduce((a: number, b: number) => a + b, 0);
                                            const mean = sum / values.length;
                                            const sorted = [...values].sort((a, b) => a - b);
                                            const median = sorted.length % 2 === 0 
                                              ? (sorted[sorted.length / 2 - 1] + sorted[sorted.length / 2]) / 2 
                                              : sorted[Math.floor(sorted.length / 2)];
                                            const min = Math.min(...values);
                                            const max = Math.max(...values);
                                            const variance = values.reduce((acc: number, val: number) => acc + Math.pow(val - mean, 2), 0) / values.length;
                                            const stdDev = Math.sqrt(variance);
                                            
                                            return (
                                              <div key={key} className="border-l-2 border-gray-700 pl-3">
                                                <div className="text-gray-300 mb-1 font-mono">{key}</div>
                                                <div className="grid grid-cols-2 gap-x-4 gap-y-1">
                                                  <div>Count: {values.length}</div>
                                                  <div>Mean: {mean.toFixed(2)}</div>
                                                  <div>Median: {median.toFixed(2)}</div>
                                                  <div>Std Dev: {stdDev.toFixed(2)}</div>
                                                  <div>Min: {min.toFixed(2)}</div>
                                                  <div>Max: {max.toFixed(2)}</div>
                                                </div>
                                              </div>
                                            );
                                          })}
                                          
                                          {/* Categorical Column Summary */}
                                          {Object.keys(message.data.data[0]).map(key => {
                                            const values = message.data.data.map((row: any) => row[key]).filter((v: any) => typeof v !== 'number');
                                            if (values.length === 0) return null;
                                            
                                            const uniqueValues = [...new Set(values)];
                                            if (uniqueValues.length > 10) return null; // Skip if too many unique values
                                            
                                            return (
                                              <div key={key} className="border-l-2 border-gray-700 pl-3">
                                                <div className="text-gray-300 mb-1 font-mono">{key}</div>
                                                <div>Unique Values: {uniqueValues.length}</div>
                                                <div className="text-gray-500 text-xs mt-1">
                                                  {uniqueValues.slice(0, 5).join(', ')}
                                                  {uniqueValues.length > 5 && '...'}
                                                </div>
                                              </div>
                                            );
                                          })}
                                        </div>
                                      </div>
                                    ) : (
                                      <div className="text-xs text-gray-500">
                                        {message.data.question_type === 'WHAT' 
                                          ? 'No data available for statistical analysis' 
                                          : 'Statistical hypothesis testing is available for WHY questions only'}
                                      </div>
                                    )}
                                  </div>
                                ),
                              },
                            ]}
                          />
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Input area - always visible at bottom */}
            <div className="flex-none bg-gradient-to-r from-gray-900/80 via-gray-900/60 to-gray-900/80 backdrop-blur-sm rounded-2xl p-4 border border-gray-800/50 shadow-2xl shadow-cyan-500/5">
              <form onSubmit={handleSubmit} className="space-y-3">
                <div className="flex gap-3">
                  <div className="flex-1 relative group">
                    <input
                      type="text"
                      value={inputValue}
                      onChange={e => setInputValue(e.target.value)}
                      placeholder="Ask anything about your data..."
                      disabled={isLoading}
                      className="w-full bg-gray-800/60 border border-gray-700/50 rounded-xl px-4 py-3 text-sm
                               focus:outline-none focus:border-cyan-500/50 focus:bg-gray-800/80 transition-all
                               placeholder:text-gray-500 group-hover:border-gray-600/50"
                    />
                    {!inputValue && (
                      <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2 pointer-events-none">
                        <span className="text-xs text-gray-600">Press Enter to send</span>
                      </div>
                    )}
                  </div>
                  <button
                    type="submit"
                    disabled={isLoading || !inputValue.trim()}
                    className="px-6 py-3 bg-gradient-to-r from-cyan-500 via-blue-500 to-teal-500 rounded-xl text-sm
                             font-semibold disabled:opacity-40 disabled:cursor-not-allowed
                             hover:shadow-lg hover:shadow-cyan-500/50 hover:scale-105 active:scale-95
                             transition-all duration-200 whitespace-nowrap relative overflow-hidden group"
                  >
                    <span className="relative z-10 flex items-center gap-2">
                      {isLoading ? (
                        <>
                          <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          <span>Analyzing...</span>
                        </>
                      ) : (
                        <>
                          <span>Send</span>
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7l5 5m0 0l-5 5m5-5H6" />
                          </svg>
                        </>
                      )}
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-cyan-600 via-blue-600 to-teal-600 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
                  </button>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500 font-medium">Quick examples:</span>
                  <div className="flex flex-wrap gap-2">
                    {examplePrompts.slice(0, 3).map((prompt, i) => (
                      <button
                        key={i}
                        type="button"
                        onClick={() => setInputValue(prompt)}
                        className="px-3 py-1.5 text-xs bg-gradient-to-r from-gray-800/80 to-gray-800/60 hover:from-cyan-900/40 hover:to-blue-900/40
                                 border border-gray-700/50 hover:border-cyan-500/30 rounded-lg transition-all duration-200
                                 hover:shadow-md hover:shadow-cyan-500/10 font-medium text-gray-300 hover:text-gray-100"
                      >
                        {prompt.length > 50 ? prompt.substring(0, 47) + '...' : prompt}
                      </button>
                    ))}
                  </div>
                </div>
              </form>
            </div>
          </div>
        </div>
      </main>

      {/* Floating Agent Activity Button */}
      <div className="fixed bottom-6 right-6 z-40 group/tooltip">
        {/* Thinking bubble tooltip */}
        <div className="absolute bottom-full right-0 mb-6 opacity-0 group-hover/tooltip:opacity-100 transition-all duration-300 pointer-events-none scale-0 group-hover/tooltip:scale-100">
          <div className="relative bg-gradient-to-r from-white via-cyan-50 to-blue-50 text-gray-900 px-5 py-3 rounded-3xl shadow-2xl border-3 border-cyan-400 animate-bounce-slow whitespace-nowrap">
            <p className="text-base font-bold bg-gradient-to-r from-cyan-600 to-blue-600 bg-clip-text text-transparent">
              Wanna know how I work? 🧠✨
            </p>
            {/* Speech bubble tail */}
            <div className="absolute -bottom-3 right-8 w-6 h-6 bg-gradient-to-br from-white to-cyan-50 border-r-3 border-b-3 border-cyan-400 transform rotate-45"></div>
          </div>
        </div>
        
        <button
          onClick={() => setActivityPopupOpen(true)}
          className="relative w-24 h-24 bg-gradient-to-br from-cyan-500 via-blue-500 to-purple-600 rounded-full shadow-2xl shadow-cyan-500/60 hover:shadow-cyan-500/80 hover:scale-110 active:scale-95 transition-all duration-300 flex items-center justify-center text-6xl border-4 border-cyan-300/40 hover:border-cyan-300/60 group"
          title="View Agent Activity"
        >
          {/* Glow ring animation */}
          <span className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-400 to-purple-400 animate-pulse-ring"></span>
          
          <span className="relative transition-all duration-300">
            {/* Bear expressions based on state */}
            {isLoading ? (
              <span className="inline-block animate-bear-thinking">🐻‍❄️</span>
            ) : (
              <>
                <span className="inline-block group-hover:hidden animate-bear-idle">🐻</span>
                <span className="hidden group-hover:inline-block animate-bear-excited">🐻</span>
              </>
            )}
          </span>
          
          {agentLogs.length > 0 && (
            <span className="absolute -top-2 -left-2 bg-gradient-to-r from-pink-500 to-rose-500 text-white text-sm font-bold rounded-full w-8 h-8 flex items-center justify-center border-3 border-white shadow-lg animate-bounce-wiggle">
              {agentLogs.length > 99 ? '99+' : agentLogs.length}
            </span>
          )}
          
          {/* Processing indicator */}
          {isLoading && (
            <span className="absolute -top-2 -right-2 flex h-5 w-5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-5 w-5 bg-green-500 border-2 border-white"></span>
            </span>
          )}
        </button>

        {/* Pulsing attention grabber when idle */}
        {!isLoading && agentLogs.length === 0 && (
          <div className="absolute inset-0 rounded-full bg-cyan-400/20 animate-ping-slow pointer-events-none"></div>
        )}
      </div>

      {/* Agent Activity Popup */}
      <AgentActivityPopup
        isOpen={activityPopupOpen}
        onClose={() => setActivityPopupOpen(false)}
        logs={agentLogs}
        isProcessing={isLoading}
      />
    </div>
  );
}