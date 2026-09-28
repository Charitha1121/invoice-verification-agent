import React, { useState, useEffect } from 'react';
import { 
  X, CheckCircle2, AlertTriangle, XCircle, ShieldAlert, FileText, 
  Cpu, History, ArrowRight, RefreshCw, Send, Check, AlertCircle, FileCode
} from 'lucide-react';
import { fetchInvoiceDetails, reviewInvoice, rerunAgent } from '../services/api';

export default function InvoiceDetailModal({ invoiceId, onClose, onRefresh, userRole }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState('verdict');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [actionMessage, setActionMessage] = useState(null);

  useEffect(() => {
    if (invoiceId) {
      loadDetails();
    }
  }, [invoiceId]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const res = await fetchInvoiceDetails(invoiceId);
      setData(res);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  if (!invoiceId) return null;

  const handleAction = async (actionType) => {
    setSubmitting(true);
    setActionMessage(null);
    try {
      await reviewInvoice(invoiceId, actionType, notes);
      setSubmitting(false);
      setActionMessage(`Invoice updated to ${actionType.toUpperCase()}`);
      loadDetails();
      if (onRefresh) onRefresh();
    } catch (err) {
      setSubmitting(false);
      setActionMessage(`Error: ${err.message}`);
    }
  };

  const handleRerun = async () => {
    setLoading(true);
    try {
      await rerunAgent(invoiceId);
      loadDetails();
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-black/85 backdrop-blur-md animate-fade-in overflow-y-auto">
      <div className="glass-panel w-full max-w-5xl rounded-3xl border border-gray-700/80 shadow-2xl my-auto overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Modal Top Header */}
        <div className="px-6 py-5 bg-gray-900/90 border-b border-gray-800 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-indigo-600/10 border border-indigo-500/20 text-indigo-400 rounded-2xl">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h2 className="text-xl font-extrabold text-white font-mono">{data?.invoice_number || 'Invoice Details'}</h2>
                {data && (
                  <span className={`px-3 py-0.5 text-xs font-bold rounded-full border ${
                    data.status === 'approved_by_human' || data.status === 'auto_approved'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : data.status === 'rejected'
                      ? 'bg-rose-500/10 text-rose-400 border-rose-500/30'
                      : 'bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse'
                  }`}>
                    {data.risk_report?.overall_status || data.status.toUpperCase()}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400 mt-1">
                Vendor: <strong className="text-gray-200">{data?.vendor_name || 'Unknown'}</strong> | PO: <strong className="text-indigo-300 font-mono">{data?.po_details?.po_number || data?.po_reference || 'No PO Linked'}</strong> | Total: <strong className="text-white">{data?.amount !== null && data?.amount !== undefined ? `₹${data.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'Unreadable / Needs Entry'}</strong>
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleRerun}
              title="Re-run Agent Verification"
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition flex items-center space-x-1 text-xs border border-gray-700"
            >
              <RefreshCw className="w-4 h-4" />
              <span className="hidden sm:inline">Re-evaluate</span>
            </button>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Modal Main Navigation Sub-tabs */}
        <div className="px-6 bg-gray-900/60 border-b border-gray-800 flex space-x-4 flex-shrink-0 text-xs font-semibold">
          <button
            onClick={() => setActiveSubTab('verdict')}
            className={`py-3 border-b-2 transition ${
              activeSubTab === 'verdict'
                ? 'border-indigo-500 text-indigo-400 font-bold'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            Agent Verdict & Tool Steps
          </button>
          <button
            onClick={() => setActiveSubTab('threeway')}
            className={`py-3 border-b-2 transition ${
              activeSubTab === 'threeway'
                ? 'border-indigo-500 text-indigo-400 font-bold'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            3-Way PO Match
          </button>
          <button
            onClick={() => setActiveSubTab('ocr')}
            className={`py-3 border-b-2 transition ${
              activeSubTab === 'ocr'
                ? 'border-indigo-500 text-indigo-400 font-bold'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            Extracted JSON & OCR Text
          </button>
          <button
            onClick={() => setActiveSubTab('audit')}
            className={`py-3 border-b-2 transition ${
              activeSubTab === 'audit'
                ? 'border-indigo-500 text-indigo-400 font-bold'
                : 'border-transparent text-gray-400 hover:text-white'
            }`}
          >
            Audit Trail ({data?.audit_logs?.length || 0})
          </button>
        </div>

        {/* Modal Scrollable Body */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1 bg-gray-950/40">
          
          {loading ? (
            <div className="py-20 text-center text-gray-400">Loading invoice verification data...</div>
          ) : !data ? (
            <div className="py-20 text-center text-rose-400">Failed to load invoice details</div>
          ) : (
            <>
              {/* Tab 1: Agent Verdict & Tool Execution Steps */}
              {activeSubTab === 'verdict' && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  
                  {/* Left Column: Risk Summary Output Box */}
                  <div className="lg:col-span-6 space-y-4">
                    <div className="glass-card p-5 rounded-2xl border border-gray-800 space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Agent Risk Summary</span>
                        <span className="text-xs text-indigo-400 font-mono">Confidence: {data.risk_report?.confidence ? (data.risk_report.confidence * 100).toFixed(0) : 85}%</span>
                      </div>
                      
                      <div className="bg-gray-900 border border-gray-800 p-4 rounded-xl font-mono text-xs text-gray-200 leading-relaxed whitespace-pre-line shadow-inner">
                        {data.risk_report?.summary_text || "No risk summary generated yet."}
                      </div>
                    </div>
                  </div>

                  {/* Right Column: Step-by-Step Tool Execution Trace */}
                  <div className="lg:col-span-6 space-y-4">
                    <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Verification Tools Execution Trace</h4>
                    
                    <div className="space-y-3">
                      {data.checks?.map((chk) => (
                        <div key={chk.id} className="p-4 rounded-xl bg-gray-900 border border-gray-800 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="font-mono text-xs font-bold text-white uppercase">{chk.check_type.replace('_', ' ')}</span>
                            <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                              chk.result === 'pass'
                                ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                                : chk.result === 'fail'
                                ? 'bg-rose-500/10 text-rose-400 border border-rose-500/30'
                                : 'bg-amber-500/10 text-amber-400 border border-amber-500/30'
                            }`}>
                              {chk.result}
                            </span>
                          </div>
                          <p className="text-xs text-gray-300 font-medium">{chk.details?.summary}</p>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>
              )}

              {/* Tab 2: 3-Way Line Item Match */}
              {activeSubTab === 'threeway' && (
                <div className="space-y-6">
                  <div className="glass-card p-5 rounded-2xl border border-gray-800">
                    <h4 className="text-sm font-bold text-white mb-2">3-Way Purchase Order Line Item Matching</h4>
                    <p className="text-xs text-gray-400 mb-4">Comparing extracted invoice line items against system purchase order records</p>
                    
                    {data.po_details ? (
                      <div className="overflow-x-auto">
                        <table className="w-full text-left text-xs border border-gray-800 rounded-xl overflow-hidden">
                          <thead className="bg-gray-900 text-gray-400 uppercase font-semibold">
                            <tr>
                              <th className="px-4 py-3">Line Description</th>
                              <th className="px-4 py-3">Invoice Qty</th>
                              <th className="px-4 py-3">PO Qty</th>
                              <th className="px-4 py-3">Invoice Unit Price</th>
                              <th className="px-4 py-3">PO Agreed Price</th>
                              <th className="px-4 py-3 text-right">Variance Status</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-gray-800 text-gray-300">
                            {data.extracted_json?.line_items?.map((item, idx) => {
                              const poMatchItem = data.po_details.line_items?.[idx] || data.po_details.line_items?.[0];
                              const qtyDiff = poMatchItem ? item.quantity - poMatchItem.quantity : 0;
                              const priceDiff = poMatchItem ? item.unit_price - poMatchItem.unit_price : 0;
                              const isMismatch = priceDiff > 0 || qtyDiff > 0;

                              return (
                                <tr key={idx} className={isMismatch ? "bg-amber-500/5" : ""}>
                                  <td className="px-4 py-3 font-semibold text-white">{item.description}</td>
                                  <td className="px-4 py-3">{item.quantity}</td>
                                  <td className="px-4 py-3">{poMatchItem ? poMatchItem.quantity : 'N/A'}</td>
                                  <td className="px-4 py-3">₹{item.unit_price?.toLocaleString('en-IN')}</td>
                                  <td className="px-4 py-3">₹{poMatchItem ? poMatchItem.unit_price?.toLocaleString('en-IN') : 'N/A'}</td>
                                  <td className="px-4 py-3 text-right">
                                    {isMismatch ? (
                                      <span className="px-2 py-1 rounded text-[10px] font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                                        Price Mismatch (+₹{priceDiff.toLocaleString('en-IN')})
                                      </span>
                                    ) : (
                                      <span className="px-2 py-1 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                                        Exact Match
                                      </span>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    ) : (
                      <div className="p-8 text-center bg-gray-900 border border-gray-800 rounded-xl text-gray-400 text-xs">
                        No purchase order reference matched for this invoice.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 3: Extracted JSON & Raw OCR Text */}
              {activeSubTab === 'ocr' && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  
                  {/* Extracted JSON */}
                  <div className="space-y-2">
                    <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center space-x-1">
                      <FileCode className="w-3.5 h-3.5 text-indigo-400" />
                      <span>Extracted Structured JSON</span>
                    </h5>
                    <pre className="p-4 bg-gray-900 border border-gray-800 rounded-xl text-xs font-mono text-emerald-400 overflow-x-auto max-h-96">
                      {JSON.stringify(data.extracted_json, null, 2)}
                    </pre>
                  </div>

                  {/* Raw OCR Text */}
                  <div className="space-y-2">
                    <h5 className="text-xs font-bold text-gray-400 uppercase tracking-wider flex items-center space-x-1">
                      <FileText className="w-3.5 h-3.5 text-blue-400" />
                      <span>Raw OCR Extracted Text</span>
                    </h5>
                    <pre className="p-4 bg-gray-900 border border-gray-800 rounded-xl text-xs font-mono text-gray-300 overflow-x-auto max-h-96 whitespace-pre-wrap">
                      {data.raw_ocr_text || "No raw OCR text captured."}
                    </pre>
                  </div>

                </div>
              )}

              {/* Tab 4: Audit Trail */}
              {activeSubTab === 'audit' && (
                <div className="space-y-4">
                  <h4 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Immutable Audit Trail Log</h4>
                  <div className="space-y-3">
                    {data.audit_logs?.map((log) => (
                      <div key={log.id} className="p-4 bg-gray-900 border border-gray-800 rounded-xl flex items-start space-x-3">
                        <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg">
                          <History className="w-4 h-4" />
                        </div>
                        <div className="flex-1">
                          <div className="flex justify-between">
                            <span className="text-xs font-bold text-white">{log.actor}</span>
                            <span className="text-[10px] text-gray-500 font-mono">{log.timestamp}</span>
                          </div>
                          <p className="text-xs text-indigo-300 font-semibold mt-0.5">{log.action}</p>
                          {log.notes && <p className="text-xs text-gray-400 mt-1 italic">{log.notes}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}

        </div>

        {/* Modal Human Action Bar (Bottom Footer) */}
        {data && (
          <div className="p-5 bg-gray-900 border-t border-gray-800 flex-shrink-0 space-y-3">
            
            {actionMessage && (
              <div className="p-2.5 bg-indigo-500/10 border border-indigo-500/30 rounded-xl text-indigo-300 text-xs font-bold flex items-center justify-between">
                <span>{actionMessage}</span>
              </div>
            )}

            <div className="flex flex-col sm:flex-row items-center gap-3">
              <input
                type="text"
                placeholder="Optional audit notes / reason for decision..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full sm:flex-1 px-4 py-2.5 bg-gray-950 border border-gray-700 rounded-xl text-xs text-white placeholder-gray-500 focus:outline-none focus:border-indigo-500"
              />

              <div className="flex items-center space-x-2 w-full sm:w-auto">
                <button
                  disabled={submitting}
                  onClick={() => handleAction('approve')}
                  className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-extrabold flex items-center justify-center space-x-1.5 shadow-lg shadow-emerald-600/30 transition active:scale-95"
                >
                  <Check className="w-4 h-4" />
                  <span>Approve Payment</span>
                </button>

                <button
                  disabled={submitting}
                  onClick={() => handleAction('flag')}
                  className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-amber-600 hover:bg-amber-500 text-white text-xs font-extrabold flex items-center justify-center space-x-1.5 shadow-lg shadow-amber-600/30 transition active:scale-95"
                >
                  <AlertCircle className="w-4 h-4" />
                  <span>Escalate Flag</span>
                </button>

                <button
                  disabled={submitting}
                  onClick={() => handleAction('reject')}
                  className="flex-1 sm:flex-none px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-extrabold flex items-center justify-center space-x-1.5 shadow-lg shadow-rose-600/30 transition active:scale-95"
                >
                  <X className="w-4 h-4" />
                  <span>Reject Invoice</span>
                </button>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
