import React, { useState, useEffect } from 'react';
import { ShieldCheck, FileCheck, Layers } from 'lucide-react';
import { fetchPurchaseOrders } from '../services/api';

export default function PurchaseOrdersView() {
  const [pos, setPos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPurchaseOrders()
      .then(data => {
        setPos(data);
        setLoading(false);
      })
      .catch(err => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="py-20 text-center text-gray-400">Loading purchase order registry...</div>;
  }

  return (
    <div className="space-y-6">
      
      <div>
        <h2 className="text-xl font-extrabold text-white flex items-center space-x-2">
          <ShieldCheck className="w-6 h-6 text-indigo-400" />
          <span>Purchase Order (PO) Registry</span>
        </h2>
        <p className="text-xs text-gray-400 mt-1">
          Authorized procurement contracts used for automated 3-way matching
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {pos.map((po) => (
          <div key={po.id} className="glass-panel p-5 rounded-2xl border border-gray-800 space-y-4">
            
            <div className="flex justify-between items-start border-b border-gray-800 pb-3">
              <div>
                <span className="px-2.5 py-1 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/30 font-mono text-xs font-bold">
                  {po.po_number}
                </span>
                <h4 className="text-sm font-bold text-white mt-2">{po.vendor_name}</h4>
              </div>
              <div className="text-right">
                <span className="text-[10px] text-gray-400 uppercase font-semibold">Agreed PO Total</span>
                <h3 className="text-lg font-extrabold text-emerald-400 mt-0.5">
                  ₹{po.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </h3>
              </div>
            </div>

            <div className="space-y-2">
              <h5 className="text-[11px] font-bold text-gray-400 uppercase tracking-wider">Agreed Line Items</h5>
              <div className="bg-gray-900 border border-gray-800 rounded-xl p-3 space-y-2">
                {po.line_items?.map((item, idx) => (
                  <div key={idx} className="flex justify-between text-xs text-gray-300">
                    <span>{item.description} (x{item.quantity})</span>
                    <span className="font-mono text-white">₹{item.total?.toLocaleString('en-IN')}</span>
                  </div>
                ))}
              </div>
            </div>

          </div>
        ))}
      </div>

    </div>
  );
}
