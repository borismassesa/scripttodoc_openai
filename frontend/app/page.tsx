'use client';

import { useState, useEffect } from 'react';
import { FileSpreadsheet, Sparkles } from 'lucide-react';
import UploadForm, { type UploadConfig } from '@/components/UploadForm';
import Tabs, { type TabId } from '@/components/Tabs';
import ActiveJobs from '@/components/ActiveJobs';
import HistoryJobs from '@/components/JobList';
import SidebarProfile from '@/components/SidebarProfile';
import { uploadTranscript, getAllJobs, type JobStatus } from '@/lib/api';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import { useAuth } from '@/lib/auth';

export default function Home() {
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabId>('create');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [activeJobsCount, setActiveJobsCount] = useState(0);
  const [justUploadedJobId, setJustUploadedJobId] = useState<string | null>(null);

  // Fetch active jobs count for badge
  useEffect(() => {
    let isMounted = true;
    let abortController: AbortController | null = null;
    
    const fetchActiveJobsCount = async () => {
      // Cancel previous request if still pending
      if (abortController) {
        abortController.abort();
      }
      
      abortController = new AbortController();
      
      try {
        const allJobs = await getAllJobs(10, abortController.signal); // Fetch fewer jobs for faster response
        if (!isMounted) return;
        
        const active = allJobs.filter(
          (job) => job.status === 'queued' || job.status === 'processing'
        );
        setActiveJobsCount(active.length);
      } catch (err: any) {
        if (!isMounted) return;
        
        // Silently handle aborted/canceled requests and timeouts - don't log or show errors
        if (
          err?.name === 'AbortError' || 
          err?.name === 'CanceledError' ||
          err?.code === 'ECONNABORTED' || 
          err?.message === 'canceled' ||
          err?.message?.includes('timeout') ||
          err?.message?.includes('aborted') ||
          err?.isCanceled
        ) {
          // Request was cancelled or timed out - this is expected, don't log
          return;
        }
        
        // Only log unexpected errors (not timeouts)
        console.warn('Failed to fetch active jobs count:', err?.message || err);
        // Keep the existing count on error instead of resetting to 0
      }
    };

    fetchActiveJobsCount();
    // ⭐ FIXED: Poll every 5 seconds for responsive badge updates
    const interval = setInterval(fetchActiveJobsCount, 5000);
    
    return () => {
      isMounted = false;
      clearInterval(interval);
      if (abortController) {
        abortController.abort();
      }
    };
  }, [refreshTrigger]);

  const handleUpload = async (files: File[], config: UploadConfig) => {
    console.log('handleUpload called', { filesCount: files.length, config });
    setError(null);
    setIsProcessing(true);

    try {
      let lastJobId: string | null = null;
      const uploadedJobs: string[] = [];

      // Upload files sequentially to avoid overwhelming the backend
      for (let i = 0; i < files.length; i++) {
        const file = files[i];
        console.log(`Uploading file ${i + 1}/${files.length}: ${file.name}`);

        try {
          const response = await uploadTranscript(file, {
            tone: config.tone,
            audience: config.audience,
            document_title: config.document_title || file.name.replace(/\.[^/.]+$/, ''),
            include_statistics: true,
            knowledge_urls: config.knowledge_urls,
          });

          console.log(`Upload ${i + 1}/${files.length} successful:`, response);
          uploadedJobs.push(response.job_id);
          lastJobId = response.job_id;
        } catch (fileErr: any) {
          console.error(`Failed to upload file ${file.name}:`, fileErr);
          // Continue with remaining files but log the error
          setError(`Some files failed to upload. ${file.name}: ${fileErr.response?.data?.detail || fileErr.message}`);
        }
      }

      if (uploadedJobs.length > 0) {
        console.log(`Successfully uploaded ${uploadedJobs.length}/${files.length} files`);

        // Track the last job for optimistic UI
        if (lastJobId) {
          setJustUploadedJobId(lastJobId);
        }

        // Trigger refresh
        setRefreshTrigger(prev => prev + 1);

        // Switch to active tab immediately
        setActiveTab('active');
      } else {
        throw new Error('All file uploads failed');
      }

      // Set processing to false
      setTimeout(() => {
        setIsProcessing(false);
      }, 300);
    } catch (err: any) {
      console.error('Upload process failed:', err);
      console.error('Error details:', {
        message: err.message,
        response: err.response,
        stack: err.stack
      });
      setError(err.response?.data?.detail || err.message || 'Failed to upload transcripts. Please try again.');
      setIsProcessing(false);
    }
  };

  const handleJobComplete = (job: JobStatus) => {
    // Refresh both active and history lists immediately
    setRefreshTrigger(prev => prev + 1);

    // Clear the optimistic job ID if it matches the completed job
    if (justUploadedJobId === job.job_id) {
      setJustUploadedJobId(null);
    }
  };

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-linear-to-br from-blue-50 via-white to-purple-50 flex flex-col">
        {/* Main Content with Sidebar */}
      <main className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Fixed */}
        <aside className="w-72 bg-linear-to-b from-white to-gray-50/50 border-r border-gray-200/80 shadow-lg h-screen flex flex-col relative">
          <div className="flex-1 overflow-y-auto">
            <div className="pt-6 pb-6">
              {/* Sidebar Header */}
              <div className="px-5 pb-5 mb-5 border-b border-gray-200/60">
                <div className="flex items-center space-x-3">
                  <div className="relative shrink-0">
                    <div className="bg-linear-to-br from-blue-500 to-blue-600 p-2 rounded-lg shadow-sm">
                      <FileSpreadsheet className="h-5 w-5 text-white" />
                      <Sparkles className="h-3 w-3 text-yellow-300 absolute -top-0.5 -right-0.5" />
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <h2 className="text-lg font-bold text-gray-900 truncate">
                      ScriptToDoc
                    </h2>
                    <p className="text-xs text-gray-500 leading-snug truncate mt-0.5">
                      AI-Powered Training Document Generator
                    </p>
                  </div>
                </div>
              </div>
              
              {/* Navigation Section */}
              <div className="px-3">
                <Tabs 
                  activeTab={activeTab} 
                  onTabChange={setActiveTab}
                  activeJobsCount={activeJobsCount}
                />
              </div>
            </div>
          </div>

          {/* Profile Section - Fixed at bottom */}
          <SidebarProfile
            userName={user?.name || 'User'}
            userEmail={user?.email || 'user@example.com'}
            onLogout={logout}
          />
        </aside>

        {/* Main Content Area - Scrollable */}
        <div className="flex-1 overflow-y-auto h-screen">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <div className="space-y-8">
              {/* Hero Section */}
              <div className="bg-linear-to-br from-[#0078D4] via-[#106EBE] to-[#005A9E] rounded-xl shadow-md p-8 text-white border border-blue-700/20">
                <h2 className="text-2xl font-semibold mb-3 tracking-tight">Transform Transcripts into Training Docs</h2>
                <p className="text-blue-50/90 text-[15px] leading-relaxed">
                  Upload a meeting transcript and get a professional training document with step-by-step instructions, confidence scores, and source citations.
                </p>
              </div>

              {/* Error Display */}
              {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <div className="shrink-0">
                      <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-red-800">Upload Failed</h3>
                      <p className="mt-1 text-sm text-red-700">{error}</p>
                    </div>
                    <button
                      onClick={() => setError(null)}
                      className="shrink-0 text-red-400 hover:text-red-600"
                    >
                      <span className="sr-only">Dismiss</span>
                      <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                      </svg>
                    </button>
                  </div>
                </div>
              )}

              {/* Tab Content */}
              {activeTab === 'create' && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <h3 className="text-xl font-semibold text-gray-900 mb-6">
                    Upload Transcript
                  </h3>
                  <UploadForm 
                    onUpload={handleUpload}
                    isProcessing={isProcessing}
                  />
                </div>
              )}

              {activeTab === 'active' && (
                <ActiveJobs
                  refreshTrigger={refreshTrigger}
                  onJobComplete={handleJobComplete}
                  onNavigateToCreate={() => setActiveTab('create')}
                  justUploadedJobId={justUploadedJobId}
                  onJobAppeared={() => setJustUploadedJobId(null)}
                />
              )}

              {activeTab === 'history' && (
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <HistoryJobs 
                    refreshTrigger={refreshTrigger}
                  />
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
      </div>
    </ProtectedRoute>
  );
}
