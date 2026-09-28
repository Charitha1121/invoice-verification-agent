import React, { useState } from 'react';
import { 
  AlertTriangle, CheckCircle2, XCircle, Clock, Eye, FileText, 
  TrendingUp, ShieldAlert, ArrowUpRight, Filter
} from 'lucide-react';

export default function InvoiceQueue({ invoices, onSelectInvoice, onOpenUpload }) {
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');

  const filtered = invoices.filter(inv => {
    if (filter === 'flagged' && !['flagged', 'pending', 'extraction_failed'].includes(inv.status)) return false;
    if (filter === 'approved' && !['approved_by_human', 'auto_approved'].includes(inv.status)) return false;
    if (filter === 'rejected' && inv.status !== 'rejected') return false;

    if (search) {
      const q = search.toLowerCase();
      return (
        (inv.invoice_number && inv.invoice_number.toLowerCase().includes(q)) ||
        (inv.vendor_name && inv.vendor_name.toLowerCase().includes(q)) ||
        (inv.po_number && inv.po_number.toLowerCase().includes(q))
      );
    }
    return true;
  });

  const totalValue = invoices
    .filter(i => ['approved_by_human', 'auto_approved'].includes(i.status))
    .reduce((acc, curr) => acc + (curr.amount || 0), 0);

  const flaggedCount = invoices.filter(i => ['flagged', 'pending', 'extraction_failed'].includes(i.status)).length;
  const approvedCount = invoices.filter(i => ['approved_by_human', 'auto_approved'].includes(i.status)).length;

  const getStatusBadge = (status, riskSummary) => {
    switch (status) {
      case 'extraction_failed':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-rose-500/20 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-rose-400" />
            EXTRACTION FAILED
          </span>
        );
      case 'flagged':
      case 'pending':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 animate-pulse">
            <AlertTriangle className="w-3.5 h-3.5 mr-1 text-amber-400" />
            HUMAN REVIEW REQUIRED
          </span>
        );
      case 'approved_by_human':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-emerald-400" />
            APPROVED BY HUMAN
          </span>
        );
      case 'auto_approved':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-blue-500/10 text-blue-400 border border-blue-500/30">
            <CheckCircle2 className="w-3.5 h-3.5 mr-1 text-blue-400" />
            AUTO APPROVED
          </span>
        );
      case 'rejected':
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <XCircle className="w-3.5 h-3.5 mr-1 text-rose-400" />
            REJECTED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-bold bg-gray-700 text-gray-300">
            <Clock className="w-3.5 h-3.5 mr-1" />
            PENDING
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Flagged Exceptions</p>
              <h3 className="text-3xl font-extrabold text-amber-400 mt-2">{flaggedCount}</h3>
            </div>
            <div className="p-3 bg-amber-500/10 rounded-xl border border-amber-500/20 text-amber-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-amber-400/80 mt-3 flex items-center">
            <span>Requires human verification</span>
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Approved Payment Value</p>
              <h3 className="text-3xl font-extrabold text-emerald-400 mt-2">
                ₹{totalValue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
              </h3>
            </div>
            <div className="p-3 bg-emerald-500/10 rounded-xl border border-emerald-500/20 text-emerald-400">
              <TrendingUp className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-emerald-400/80 mt-3 flex items-center">
            <span>{approvedCount} invoices verified & cleared</span>
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden">
          <div className="flex justify-between items-start">
            <div>
              <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Total Invoices Processed</p>
              <h3 className="text-3xl font-extrabold text-white mt-2">{invoices.length}</h3>
            </div>
            <div className="p-3 bg-blue-500/10 rounded-xl border border-blue-500/20 text-blue-400">
              <FileText className="w-6 h-6" />
            </div>
          </div>
          <p className="text-xs text-gray-400 mt-3 flex items-center">
            <span>Deterministic + AI OCR Pipeline</span>
          </p>
        </div>

        <div className="glass-panel p-5 rounded-2xl border border-gray-800 relative overflow-hidden flex flex-col justify-between">
          <div>
            <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Quick Action</p>
            <p className="text-xs text-gray-300 mt-1">Upload scan PDF/Image or load sample preset</p>
          </div>
          <button
            onClick={onOpenUpload}
            className="w-full mt-3 py-2.5 px-4 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-xs flex items-center justify-center space-x-2 transition shadow-lg shadow-indigo-600/30"
          >
            <span>+ Ingest New Invoice</span>
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>

      </div>

      {/* Filter Bar & Search */}
      <div className="glass-panel p-4 rounded-2xl border border-gray-800 flex flex-col sm:flex-row justify-between items-center gap-4">
        
        {/* Filter Pills */}
        <div className="flex items-center space-x-2 w-full sm:w-auto overflow-x-auto">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
              filter === 'all'
                ? 'bg-indigo-600 text-white shadow'
                : 'text-gray-400 hover:text-white bg-gray-800/40'
            }`}
          >
            All Invoices ({invoices.length})
          </button>
          
          <button
            onClick={() => setFilter('flagged')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1 ${
              filter === 'flagged'
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 shadow'
                : 'text-gray-400 hover:text-white bg-gray-800/40'
            }`}
          >
            <AlertTriangle className="w-3 h-3 text-amber-400" />
            <span>Pending Review ({flaggedCount})</span>
          </button>

          <button
            onClick={() => setFilter('approved')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1 ${
              filter === 'approved'
                ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shadow'
                : 'text-gray-400 hover:text-white bg-gray-800/40'
            }`}
          >
            <CheckCircle2 className="w-3 h-3 text-emerald-400" />
            <span>Approved ({approvedCount})</span>
          </button>

          <button
            onClick={() => setFilter('rejected')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition flex items-center space-x-1 ${
              filter === 'rejected'
                ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 shadow'
                : 'text-gray-400 hover:text-white bg-gray-800/40'
            }`}
          >
            <XCircle className="w-3 h-3 text-rose-400" />
            <span>Rejected</span>
          </button>
        </div>

        {/* Search Input */}
        <div className="relative w-full sm:w-64">
          <input
            type="text"
            placeholder="Search vendor, INV, PO..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 bg-gray-900 border border-gray-700 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500 transition"
          />
          <Filter className="w-3.5 h-3.5 text-gray-500 absolute left-3 top-2.5" />
        </div>

      </div>

      {/* Main Invoices Table */}
      <div className="glass-panel rounded-2xl border border-gray-800 overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            
            <thead className="bg-gray-900/80 text-gray-400 font-semibold uppercase tracking-wider border-b border-gray-800">
              <tr>
                <th className="px-6 py-4">Invoice #</th>
                <th className="px-6 py-4">Vendor</th>
                <th className="px-6 py-4">PO Reference</th>
                <th className="px-6 py-4">Amount (INR)</th>
                <th className="px-6 py-4">Agent Verdict & Status</th>
                <th className="px-6 py-4 text-center">Action</th>
              </tr>
            </thead>

            <tbody className="divide-y divide-gray-800/60 text-gray-300">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center py-12 text-gray-500 font-medium">
                    No invoices found matching criteria. Click "+ Ingest New Invoice" to test.
                  </td>
                </tr>
              ) : (
                filtered.map((inv) => (
                  <tr 
                    key={inv.id} 
                    onClick={() => onSelectInvoice(inv.id)}
                    className="hover:bg-gray-800/40 transition cursor-pointer group"
                  >
                    
                    {/* Invoice Number */}
                    <td className="px-6 py-4 font-mono font-bold text-white group-hover:text-indigo-400 transition flex flex-col">
                      <span>{inv.invoice_number || 'Unreadable Invoice #'}</span>
                      <span className="text-[10px] text-gray-500 font-sans font-normal mt-0.5">{inv.file_name || 'Uploaded PDF'}</span>
                    </td>

                    {/* Vendor */}
                    <td className="px-6 py-4 font-semibold text-gray-200">
                      {inv.vendor_name || 'Unknown Vendor'}
                    </td>

                    {/* PO Reference */}
                    <td className="px-6 py-4">
                      {inv.po_number && inv.po_number.toUpperCase() !== "REFERENCE" && inv.po_number.toUpperCase() !== "ORDER" ? (
                        <span className="px-2 py-1 rounded bg-gray-800 font-mono text-indigo-300 border border-gray-700">
                          {inv.po_number}
                        </span>
                      ) : (
                        <span className="text-gray-500 italic">No PO Linked</span>
                      )}
                    </td>

                    {/* Amount */}
                    <td className="px-6 py-4 font-extrabold text-white text-sm">
                      {inv.amount !== null && inv.amount !== undefined ? (
                        <span>₹{inv.amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                      ) : (
                        <span className="text-amber-400 font-bold italic text-xs">Unreadable / Needs Entry</span>
                      )}
                    </td>

                    {/* Verdict Status */}
                    <td className="px-6 py-4">
                      {getStatusBadge(inv.status, inv.risk_summary)}
                    </td>

                    {/* Action Button */}
                    <td className="px-6 py-4 text-center">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectInvoice(inv.id);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-gray-800 hover:bg-indigo-600 text-gray-300 hover:text-white font-semibold transition border border-gray-700 flex items-center justify-center space-x-1.5 mx-auto shadow-sm"
                      >
                        <Eye className="w-3.5 h-3.5" />
                        <span>Inspect & Review</span>
                      </button>
                    </td>

                  </tr>
                ))
              )}
            </tbody>

          </table>
        </div>
      </div>

    </div>
  );
}
