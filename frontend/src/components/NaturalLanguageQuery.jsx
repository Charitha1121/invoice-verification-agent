import React, { useState } from 'react';
import { Search, Sparkles, ArrowRight, FileText } from 'lucide-react';
import { queryInvoicesNL } from '../services/api';

export default function NaturalLanguageQuery({ onSelectInvoice }) {
  const [queryText, setQueryText] = useState('Show me all invoices flagged for PO mismatch');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSearch = async (e) => {
    if (e) e.preventDefault();
    if (!queryText.trim()) return;
    setLoading(true);
    try {
      const res = await queryInvoicesNL(queryText);
      setResults(res);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const sampleQueries = [
    "Show me all invoices flagged for PO mismatch",
    "Find invoices over ₹1,00,000",
    "Show approved invoices for ABC Technologies",
    "Find duplicate invoices"
  ];

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      
      {/* Header */}
      <div className="text-center space-y-2">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 text-xs font-semibold">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Natural Language Invoices Search Engine</span>
        </div>
        <h2 className="text-2xl font-extrabold text-white">Ask Anything About Your Invoices Database</h2>
        <p className="text-xs text-gray-400">Query exceptions, PO mismatches, amounts, and vendor trends using plain English</p>
      </div>

      {/* Query Bar */}
      <form onSubmit={handleSearch} className="glass-panel p-2 rounded-2xl border border-gray-700/80 shadow-2xl flex items-center space-x-2">
        <Search className="w-5 h-5 text-gray-400 ml-3 flex-shrink-0" />
        <input
          type="text"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
          placeholder="e.g. Show me all invoices flagged for PO mismatch over ₹1,00,000"
          className="w-full bg-transparent py-3 px-2 text-sm text-white placeholder-gray-500 focus:outline-none font-medium"
        />
        <button
          type="submit"
          className="px-5 py-3 bg-gradient-to-r from-indigo-600 to-blue-600 hover:from-indigo-500 hover:to-blue-500 text-white rounded-xl text-xs font-extrabold flex items-center space-x-2 shadow-lg transition active:scale-95 flex-shrink-0"
        >
          <span>Query AI</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </form>

      {/* Preset Prompt Pills */}
      <div className="flex flex-wrap items-center justify-center gap-2">
        <span className="text-[11px] font-semibold text-gray-500">Sample Queries:</span>
        {sampleQueries.map((sq, idx) => (
          <button
            key={idx}
            onClick={() => {
              setQueryText(sq);
              queryInvoicesNL(sq).then(r => setResults(r));
            }}
            className="px-3 py-1 rounded-full bg-gray-900 hover:bg-gray-800 text-xs text-gray-300 border border-gray-800 transition"
          >
            "{sq}"
          </button>
        ))}
      </div>

      {/* Results Section */}
      {loading ? (
        <div className="py-12 text-center text-gray-400">Parsing natural language prompt...</div>
      ) : results ? (
        <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
          <div className="flex justify-between items-center border-b border-gray-800 pb-3">
            <h4 className="text-sm font-bold text-white">Matched Invoices ({results.matched_count})</h4>
            <span className="text-xs text-indigo-400 font-mono">Query: "{results.query}"</span>
          </div>

          <div className="space-y-3">
            {results.results.length === 0 ? (
              <p className="text-xs text-gray-500 py-6 text-center">No invoices matched query parameters.</p>
            ) : (
              results.results.map((inv) => (
                <div
                  key={inv.id}
                  onClick={() => onSelectInvoice(inv.id)}
                  className="p-4 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded-xl flex items-center justify-between transition cursor-pointer"
                >
                  <div className="flex items-center space-x-3">
                    <div className="p-2.5 bg-indigo-500/10 text-indigo-400 rounded-xl">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-mono text-xs font-bold text-white">{inv.invoice_number}</span>
                        <span className="text-xs text-gray-400">({inv.vendor_name})</span>
                      </div>
                      <p className="text-xs text-amber-400 mt-1 font-medium">{inv.risk_summary}</p>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-sm font-extrabold text-white">₹{inv.amount?.toLocaleString('en-IN')}</span>
                    <p className="text-[10px] text-gray-500 mt-0.5">{inv.invoice_date || 'N/A'}</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}

    </div>
  );
}
