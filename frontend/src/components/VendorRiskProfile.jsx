import React, { useState, useEffect } from 'react';
import { Building2, TrendingUp, AlertTriangle, ShieldCheck, FileText, CheckCircle2 } from 'lucide-react';
import { fetchVendors, fetchVendorProfile } from '../services/api';

export default function VendorRiskProfile({ onSelectInvoice }) {
  const [vendors, setVendors] = useState([]);
  const [selectedVendorId, setSelectedVendorId] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadVendors();
  }, []);

  const loadVendors = async () => {
    try {
      const data = await fetchVendors();
      setVendors(data);
      if (data.length > 0) {
        setSelectedVendorId(data[0].id);
        loadProfile(data[0].id);
      }
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const loadProfile = async (id) => {
    try {
      const res = await fetchVendorProfile(id);
      setProfile(res);
    } catch (err) {
      console.error(err);
    }
  };

  const handleSelectVendor = (id) => {
    setSelectedVendorId(id);
    loadProfile(id);
  };

  if (loading) {
    return <div className="py-20 text-center text-gray-400">Loading vendor risk profiles...</div>;
  }

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-xl font-extrabold text-white flex items-center space-x-2">
          <Building2 className="w-6 h-6 text-indigo-400" />
          <span>Vendor Risk Directory & Analytics</span>
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Historical billing statistics, rolling average metrics, and exception frequency per supplier
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Left Side: Vendor Directory List */}
        <div className="lg:col-span-4 space-y-3">
          <h3 className="text-xs font-bold text-gray-400 uppercase tracking-wider">Registered Vendors</h3>
          <div className="space-y-2">
            {vendors.map((v) => (
              <button
                key={v.id}
                onClick={() => handleSelectVendor(v.id)}
                className={`w-full p-4 rounded-2xl border text-left transition ${
                  selectedVendorId === v.id
                    ? 'bg-indigo-600/20 border-indigo-500 text-white shadow-lg'
                    : 'bg-gray-900 border-gray-800 text-gray-300 hover:bg-gray-800/60'
                }`}
              >
                <div className="flex justify-between items-start">
                  <h4 className="font-bold text-sm truncate">{v.name}</h4>
                  {v.flagged_count > 0 ? (
                    <span className="px-2 py-0.5 text-[10px] font-extrabold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full">
                      {v.flagged_count} Flagged
                    </span>
                  ) : (
                    <span className="px-2 py-0.5 text-[10px] font-extrabold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full">
                      Low Risk
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-400 mt-2 font-mono">GST: {v.gst_number || 'N/A'}</p>
                <div className="flex justify-between items-center mt-3 text-xs text-gray-400 pt-2 border-t border-gray-800/60">
                  <span>Invoices: {v.invoice_count}</span>
                  <span className="font-bold text-white">Spent: ₹{v.total_spent?.toLocaleString('en-IN')}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Right Side: Vendor Detailed Risk Profile */}
        <div className="lg:col-span-8 space-y-6">
          {profile ? (
            <>
              {/* Profile Card */}
              <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-6">
                
                <div className="flex justify-between items-start border-b border-gray-800 pb-4">
                  <div>
                    <h3 className="text-2xl font-extrabold text-white">{profile.name}</h3>
                    <p className="text-xs font-mono text-indigo-400 mt-1">GSTIN: {profile.gst_number || 'Not Registered'}</p>
                  </div>
                  <div className="text-right">
                    <span className="text-xs text-gray-400">Exception Rate</span>
                    <h4 className={`text-2xl font-extrabold ${
                      profile.metrics.mismatch_rate_percent > 30 ? 'text-rose-400' : profile.metrics.mismatch_rate_percent > 0 ? 'text-amber-400' : 'text-emerald-400'
                    }`}>
                      {profile.metrics.mismatch_rate_percent}%
                    </h4>
                  </div>
                </div>

                {/* Metrics Grid */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  
                  <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <p className="text-[11px] font-semibold text-gray-400 uppercase">Rolling Avg Invoice</p>
                    <h4 className="text-lg font-extrabold text-white mt-1">
                      ₹{profile.metrics.avg_invoice_amount?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </h4>
                  </div>

                  <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <p className="text-[11px] font-semibold text-gray-400 uppercase">Total Cleared Spend</p>
                    <h4 className="text-lg font-extrabold text-emerald-400 mt-1">
                      ₹{profile.metrics.total_spent?.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                    </h4>
                  </div>

                  <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <p className="text-[11px] font-semibold text-gray-400 uppercase">Processed Invoices</p>
                    <h4 className="text-lg font-extrabold text-indigo-400 mt-1">
                      {profile.metrics.total_invoices}
                    </h4>
                  </div>

                  <div className="p-4 bg-gray-900 rounded-xl border border-gray-800">
                    <p className="text-[11px] font-semibold text-gray-400 uppercase">System PO Count</p>
                    <h4 className="text-lg font-extrabold text-blue-400 mt-1">
                      {profile.metrics.total_pos_count}
                    </h4>
                  </div>

                </div>

              </div>

              {/* Vendor Recent Invoices */}
              <div className="glass-panel p-6 rounded-2xl border border-gray-800 space-y-4">
                <h4 className="text-sm font-bold text-white">Recent Invoices for {profile.name}</h4>
                <div className="space-y-2">
                  {profile.recent_invoices.map((inv) => (
                    <div
                      key={inv.id}
                      onClick={() => onSelectInvoice(inv.id)}
                      className="p-3.5 bg-gray-900 hover:bg-gray-800 border border-gray-800 rounded-xl flex items-center justify-between transition cursor-pointer"
                    >
                      <div>
                        <span className="font-mono text-xs font-bold text-white">{inv.invoice_number}</span>
                        <p className="text-[11px] text-gray-400 mt-0.5">{inv.date || inv.created_at}</p>
                      </div>
                      <div className="text-right">
                        <span className="text-xs font-extrabold text-white">₹{inv.amount?.toLocaleString('en-IN')}</span>
                        <div className="mt-0.5">
                          <span className={`px-2 py-0.5 text-[10px] font-bold rounded uppercase ${
                            inv.status.includes('approved') ? 'text-emerald-400 bg-emerald-500/10' : 'text-amber-400 bg-amber-500/10'
                          }`}>
                            {inv.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </>
          ) : (
            <div className="py-20 text-center text-gray-400">Select a vendor from the left list to view profile details.</div>
          )}
        </div>

      </div>

    </div>
  );
}
