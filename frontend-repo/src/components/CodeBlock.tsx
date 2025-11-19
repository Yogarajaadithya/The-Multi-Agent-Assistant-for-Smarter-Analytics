import { useState } from 'react';
import { ClipboardDocumentIcon, ClipboardDocumentCheckIcon } from '@heroicons/react/24/outline';

type Props = {
  code: string;
  language?: string;
};

export default function CodeBlock({ code, language = 'sql' }: Props) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  // Format SQL to be more readable
  const formatCode = (code: string, lang: string) => {
    if (lang === 'sql') {
      // Add line breaks after common SQL keywords for better readability
      return code
        .replace(/\s+(SELECT|FROM|WHERE|GROUP BY|ORDER BY|HAVING|JOIN|LEFT JOIN|RIGHT JOIN|INNER JOIN|OUTER JOIN|UNION|LIMIT|OFFSET)\s+/gi, '\n$1 ')
        .replace(/,\s*(?=[a-zA-Z])/g, ',\n  ')
        .trim();
    }
    return code;
  };

  const formattedCode = formatCode(code, language);

  return (
    <div className="relative group w-full" style={{ maxWidth: '100%' }}>
      <div className="absolute top-2 left-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
        {language}
      </div>
      <pre 
        className={`language-${language} bg-gradient-to-br from-gray-900/60 to-gray-800/60 rounded-xl p-4 pt-8
                   border border-gray-700/50 shadow-lg overflow-x-auto max-w-full`} 
        style={{ maxWidth: '100%' }}
      >
        <code className="block text-sm font-mono text-gray-100 leading-relaxed whitespace-pre-wrap break-words">
          {formattedCode}
        </code>
      </pre>
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 p-2 rounded-lg bg-gray-800/80 text-gray-400 
                 hover:bg-cyan-600/80 hover:text-white transition-all
                 shadow-lg hover:shadow-cyan-500/30"
        title={copied ? 'Copied!' : 'Copy to clipboard'}
      >
        {copied ? (
          <ClipboardDocumentCheckIcon className="w-4 h-4" />
        ) : (
          <ClipboardDocumentIcon className="w-4 h-4" />
        )}
      </button>
    </div>
  );
}