import React from 'react';
import { ShieldAlert, FileText, Building2, Search, Upload, RefreshCw, Cpu, UserCheck } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, stats, onOpenUpload, userRole, setUserRole, onRefresh }) {
  return (
    <header className="sticky top-0 z-40 border-b border-gray-800 bg-gray-900/95 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Brand */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => setActiveTab('queue')}>
            <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-blue-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Cpu className="h-6 w-6 text-white animate-pulse" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg text-white tracking-tight">AP Verification Agent</span>
                <span className="px-2 py-0.5 text-xs font-semibold bg-indigo-500/20 text-indigo-400 border border-indigo-500/30 rounded-full">3-Way Match</span>
              </div>
              <p className="text-xs text-gray-400 hidden sm:block">AI-Powered Accounts Payable & Risk Engine</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex space-x-1">
            <button
              onClick={() => setActiveTab('queue')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'queue'
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <FileText className="h-4 w-4" />
              <span>Review Queue</span>
              {stats.flagged > 0 && (
                <span className="ml-1.5 px-2 py-0.5 text-xs font-bold bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded-full">
                  {stats.flagged}
                </span>
              )}
            </button>

            <button
              onClick={() => setActiveTab('vendors')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'vendors'
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Building2 className="h-4 w-4" />
              <span>Vendor Risk Profiles</span>
            </button>

            <button
              onClick={() => setActiveTab('pos')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'pos'
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <ShieldAlert className="h-4 w-4" />
              <span>PO Registry</span>
            </button>

            <button
              onClick={() => setActiveTab('nl_query')}
              className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all flex items-center space-x-2 ${
                activeTab === 'nl_query'
                  ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30 shadow-sm'
                  : 'text-gray-400 hover:text-white hover:bg-gray-800/60'
              }`}
            >
              <Search className="h-4 w-4" />
              <span>AI Search</span>
            </button>
          </nav>

          {/* Action Buttons & User Switcher */}
          <div className="flex items-center space-x-3">
            <button
              onClick={onRefresh}
              title="Sync latest DB data"
              className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-gray-800 transition"
            >
              <RefreshCw className="h-4 w-4" />
            </button>

            {/* Role Switcher Pill */}
            <div className="flex items-center bg-gray-800/80 border border-gray-700/60 rounded-lg p-1 text-xs">
              <span className="text-gray-400 px-2 font-medium flex items-center space-x-1">
                <UserCheck className="h-3.5 w-3.5 text-indigo-400" />
                <span className="hidden lg:inline">Role:</span>
              </span>
              <button
                onClick={() => setUserRole('finance_user')}
                className={`px-2 py-1 rounded font-semibold transition ${
                  userRole === 'finance_user'
                    ? 'bg-indigo-600 text-white shadow'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Finance Specialist
              </button>
              <button
                onClick={() => setUserRole('admin')}
                className={`px-2 py-1 rounded font-semibold transition ${
                  userRole === 'admin'
                    ? 'bg-purple-600 text-white shadow'
                    : 'text-gray-400 hover:text-white'
                }`}
              >
                Lead Auditor
              </button>
            </div>

            {/* Upload Button */}
            <button
              onClick={onOpenUpload}
              className="flex items-center space-x-2 px-4 py-2 rounded-lg bg-gradient-to-r from-indigo-600 to-blue-600 text-white text-sm font-semibold hover:from-indigo-500 hover:to-blue-500 shadow-md shadow-indigo-600/20 transition transform active:scale-95"
            >
              <Upload className="h-4 w-4" />
              <span className="hidden sm:inline">Upload Invoice</span>
            </button>
          </div>

        </div>
      </div>
    </header>
  );
}
