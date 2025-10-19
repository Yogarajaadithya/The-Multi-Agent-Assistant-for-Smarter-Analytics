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

  return (
    <div className="relative group">
      <pre className={`language-${language} bg-gray-900/50 rounded-lg p-4 overflow-x-auto`}>
        <code>{code}</code>
      </pre>
      <button
        onClick={copyToClipboard}
        className="absolute top-2 right-2 p-2 rounded-lg bg-gray-800/50 text-gray-400 
                 hover:bg-gray-700/50 hover:text-gray-300 transition-all"
        title={copied ? 'Copied!' : 'Copy to clipboard'}
      >
        {copied ? (
          <ClipboardDocumentCheckIcon className="w-5 h-5" />
        ) : (
          <ClipboardDocumentIcon className="w-5 h-5" />
        )}
      </button>
    </div>
  );
}