import React, { useState, useEffect } from 'react';
import { Upload, X, FileText, CheckCircle2, AlertTriangle, Sparkles, Loader2 } from 'lucide-react';
import { uploadInvoiceFile, listSamplePresets, processSamplePreset } from '../services/api';

export default function InvoiceUploadModal({ isOpen, onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [presets, setPresets] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (isOpen) {
      listSamplePresets()
        .then(res => setPresets(res))
        .catch(err => console.error("Failed to load presets", err));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const res = await uploadInvoiceFile(file);
      setLoading(false);
      onSuccess(res.invoice_id);
      onClose();
    } catch (err) {
      setLoading(false);
      setError(err.message || "Failed to process invoice upload");
    }
  };

  const handleProcessPreset = async (presetName) => {
    setLoading(true);
    setError(null);
    try {
      const res = await processSamplePreset(presetName);
      setLoading(false);
      onSuccess(res.invoice_id);
      onClose();
    } catch (err) {
      setLoading(false);
      setError(err.message || "Failed to process preset");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in">
      <div className="glass-panel w-full max-w-2xl rounded-3xl border border-gray-700/80 p-6 sm:p-8 relative shadow-2xl overflow-hidden">
        
        {/* Header */}
        <div className="flex justify-between items-start border-b border-gray-800 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              <h2 className="text-xl font-extrabold text-white">Ingest Invoice for 3-Way Verification</h2>
            </div>
            <p className="text-xs text-gray-400 mt-1">Upload a PDF/Image invoice or run a pre-configured demo scenario</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 text-gray-400 hover:text-white rounded-lg hover:bg-gray-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs font-semibold flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {loading ? (
          <div className="py-16 text-center space-y-4">
            <Loader2 className="w-12 h-12 text-indigo-500 animate-spin mx-auto" />
            <div>
              <h4 className="text-base font-bold text-white">Running OCR & Verification Agent...</h4>
              <p className="text-xs text-gray-400 mt-1">Parsing text, querying POs, executing deterministic checks & LLM synthesis</p>
            </div>
          </div>
        ) : (
          <div className="mt-6 space-y-6">
            
            {/* Custom File Dropzone */}
            <form onSubmit={handleFileUpload} className="space-y-4">
              <div className="border-2 border-dashed border-gray-700 hover:border-indigo-500 rounded-2xl p-8 text-center bg-gray-900/50 hover:bg-gray-900/80 transition cursor-pointer relative group">
                <input
                  type="file"
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setFile(e.target.files[0])}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center space-y-3">
                  <div className="p-4 bg-indigo-600/10 text-indigo-400 rounded-2xl group-hover:scale-110 transition">
                    <Upload className="w-8 h-8" />
                  </div>
                  <div>
                    <span className="text-sm font-bold text-white">
                      {file ? file.name : "Click or drag invoice PDF / Image here"}
                    </span>
                    <p className="text-xs text-gray-500 mt-1">Supports PDF, PNG, JPG, JPEG scans</p>
                  </div>
                </div>
              </div>

              {file && (
                <button
                  type="submit"
                  className="w-full py-3 bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl font-bold text-sm shadow-lg shadow-indigo-600/30 transition flex items-center justify-center space-x-2"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Execute Verification Pipeline</span>
                </button>
              )}
            </form>

            {/* Divider */}
            <div className="relative flex py-2 items-center">
              <div className="flex-grow border-t border-gray-800"></div>
              <span className="flex-shrink mx-4 text-xs font-semibold text-gray-500 uppercase tracking-widest">
                or select 1-click test preset
              </span>
              <div className="flex-grow border-t border-gray-800"></div>
            </div>

            {/* Presets List */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {presets.map((p) => (
                <button
                  key={p.filename}
                  onClick={() => handleProcessPreset(p.filename)}
                  className="p-3.5 rounded-xl bg-gray-900/80 hover:bg-gray-800 border border-gray-800 hover:border-indigo-500/50 text-left transition flex items-start space-x-3 group"
                >
                  <div className="p-2 bg-indigo-500/10 text-indigo-400 rounded-lg group-hover:bg-indigo-600 group-hover:text-white transition flex-shrink-0">
                    <FileText className="w-4 h-4" />
                  </div>
                  <div className="overflow-hidden">
                    <h5 className="text-xs font-bold text-white truncate">{p.filename}</h5>
                    <p className="text-[11px] text-gray-400 mt-0.5 line-clamp-2">{p.description}</p>
                  </div>
                </button>
              ))}
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
