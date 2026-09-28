import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import InvoiceQueue from './components/InvoiceQueue';
import VendorRiskProfile from './components/VendorRiskProfile';
import PurchaseOrdersView from './components/PurchaseOrdersView';
import NaturalLanguageQuery from './components/NaturalLanguageQuery';
import InvoiceUploadModal from './components/InvoiceUploadModal';
import InvoiceDetailModal from './components/InvoiceDetailModal';
import { fetchInvoices } from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('queue');
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState(null);
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [userRole, setUserRole] = useState('finance_user');

  useEffect(() => {
    loadInvoices();
  }, []);

  const loadInvoices = async () => {
    setLoading(true);
    try {
      const data = await fetchInvoices();
      setInvoices(data);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  };

  const handleUploadSuccess = (newInvoiceId) => {
    loadInvoices();
    if (newInvoiceId) {
      setSelectedInvoiceId(newInvoiceId);
    }
  };

  const stats = {
    total: invoices.length,
    flagged: invoices.filter(i => ['flagged', 'pending'].includes(i.status)).length,
    approved: invoices.filter(i => ['approved_by_human', 'auto_approved'].includes(i.status)).length,
  };

  return (
    <div className="min-h-screen bg-[#090D16] text-gray-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      
      {/* Top Navigation */}
      <Navbar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        stats={stats}
        onOpenUpload={() => setIsUploadOpen(true)}
        userRole={userRole}
        setUserRole={setUserRole}
        onRefresh={loadInvoices}
      />

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <div className="py-24 text-center space-y-3">
            <div className="w-10 h-10 border-4 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
            <p className="text-xs text-gray-400 font-semibold">Connecting to AP Verification Agent DB...</p>
          </div>
        ) : (
          <>
            {activeTab === 'queue' && (
              <InvoiceQueue
                invoices={invoices}
                onSelectInvoice={(id) => setSelectedInvoiceId(id)}
                onOpenUpload={() => setIsUploadOpen(true)}
              />
            )}

            {activeTab === 'vendors' && (
              <VendorRiskProfile
                onSelectInvoice={(id) => setSelectedInvoiceId(id)}
              />
            )}

            {activeTab === 'pos' && (
              <PurchaseOrdersView />
            )}

            {activeTab === 'nl_query' && (
              <NaturalLanguageQuery
                onSelectInvoice={(id) => setSelectedInvoiceId(id)}
              />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-800/60 py-6 text-center text-xs text-gray-500 bg-gray-950/80">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>AP Verification Agent — Built with FastAPI, PostgreSQL, Tesseract OCR, LLM Orchestration & React</span>
          <span className="font-mono text-gray-400">Environment: Production Sandbox</span>
        </div>
      </footer>

      {/* Modals */}
      <InvoiceUploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onSuccess={handleUploadSuccess}
      />

      <InvoiceDetailModal
        invoiceId={selectedInvoiceId}
        onClose={() => setSelectedInvoiceId(null)}
        onRefresh={loadInvoices}
        userRole={userRole}
      />

    </div>
  );
}
