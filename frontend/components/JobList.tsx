'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { FileText, Clock, CheckCircle, XCircle, Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { getAllJobs, deleteJob, type JobStatus } from '@/lib/api';
import { formatRelativeTime, getStatusColor, cn } from '@/lib/utils';
import DocumentResults from '@/components/DocumentResults';
import EmptyState from '@/components/EmptyState';

interface HistoryJobsProps {
  refreshTrigger?: number;
}

export default function HistoryJobs({ refreshTrigger }: HistoryJobsProps) {
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [statusFilter, setStatusFilter] = useState<'all' | 'completed' | 'failed'>('all');
  const [hasMore, setHasMore] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);

  const fetchJobs = useCallback(async (showLoading = false, currentLimit = 10) => {
    // Cancel previous request if still pending
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      if (showLoading) {
        setLoading(true);
      }

      // Fetch only 10 jobs initially for faster loading (reduced from 20)
      const data = await getAllJobs(currentLimit, signal);

      if (!isMountedRef.current || signal.aborted) return;

      // Filter for completed/failed jobs only
      const historyJobs = data.filter(
        (job) => job.status === 'completed' || job.status === 'failed'
      );

      // Sort by created_at descending (newest first) - backend already sorted, but ensure consistency
      historyJobs.sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      );

      setJobs(historyJobs);
      setHasMore(data.length >= currentLimit); // If we got fewer items than requested, no more to load
      setError(null);
    } catch (err: any) {
      // Silently handle timeout and canceled requests - these are expected
      if (
        signal.aborted ||
        err?.code === 'ECONNABORTED' || 
        err?.message === 'canceled' ||
        err?.message?.includes('timeout') ||
        err?.message?.includes('aborted') ||
        err?.name === 'AbortError' ||
        err?.name === 'CanceledError' ||
        err?.isCanceled
      ) {
        // Just log as info, don't show error to user
        console.info('Request timeout/canceled (will retry):', err?.message);
        return;
      }
      
      if (!isMountedRef.current) return;
      
      console.error('Failed to fetch jobs:', err);
      const errorMessage = err?.message || 'Failed to load jobs. Please ensure the backend API is running.';
      setError(errorMessage);
    } finally {
      if (isMountedRef.current && !signal.aborted) {
        setLoading(false);
      }
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return;

    setLoadingMore(true);
    const newLimit = jobs.length + 10; // Load 10 more
    await fetchJobs(false, newLimit);
    setLoadingMore(false);
  }, [loadingMore, hasMore, jobs.length, fetchJobs]);

  useEffect(() => {
    isMountedRef.current = true;

    // Initial fetch with loading state (10 items)
    fetchJobs(true, 10);

    // Poll every 30 seconds to refresh history (slower than Active tab - reduced frequency)
    // History doesn't change as often, so we can poll less frequently
    const interval = setInterval(() => {
      if (isMountedRef.current) {
        fetchJobs(false, Math.max(10, jobs.length)); // Refresh current view without showing loading state
      }
    }, 30000); // Increased from 10s to 30s

    return () => {
      isMountedRef.current = false;
      clearInterval(interval);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [refreshTrigger, fetchJobs]);

  const handleDelete = async (jobId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    
    if (!confirm('Are you sure you want to delete this job and its document?')) {
      return;
    }

    try {
      await deleteJob(jobId);
      // Use functional update to avoid stale closure
      setJobs((prevJobs) => prevJobs.filter(j => j.job_id !== jobId));
      if (selectedJobId === jobId) {
        setSelectedJobId(null);
      }
      setExpandedJobs((prev) => {
        const next = new Set(prev);
        next.delete(jobId);
        return next;
      });
    } catch (err) {
      console.error('Failed to delete job:', err);
      alert('Failed to delete job');
    }
  };

  const handleJobClick = (jobId: string) => {
    if (expandedJobs.has(jobId)) {
      setExpandedJobs((prev) => {
        const next = new Set(prev);
        next.delete(jobId);
        return next;
      });
      if (selectedJobId === jobId) {
        setSelectedJobId(null);
      }
    } else {
      setExpandedJobs((prev) => new Set(prev).add(jobId));
      setSelectedJobId(jobId);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      default:
        return <FileText className="h-5 w-5 text-gray-500" />;
    }
  };

  // Filter jobs by status
  const filteredJobs = statusFilter === 'all' 
    ? jobs 
    : jobs.filter(job => job.status === statusFilter);

  if (loading && jobs.length === 0) {
    return (
      <div className="animate-pulse space-y-4">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-20 bg-gray-200 rounded-lg"></div>
        ))}
      </div>
    );
  }

  if (error && jobs.length === 0) {
    return (
      <div className="text-red-600 space-y-2">
        <p className="font-semibold">Error loading jobs</p>
        <p className="text-sm">{error}</p>
        <p className="text-xs text-gray-500 mt-2">
          Make sure the backend API is running at http://localhost:8000
        </p>
      </div>
    );
  }

  if (filteredJobs.length === 0) {
    return (
      <EmptyState
        variant="no-history"
        title={statusFilter === 'all' ? 'No History Yet' : `No ${statusFilter.charAt(0).toUpperCase() + statusFilter.slice(1)} Jobs`}
        description={
          statusFilter === 'all'
            ? 'Completed and failed jobs will appear here after processing.'
            : `No ${statusFilter} jobs found. Try adjusting your filter or process a new document.`
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* Status Filter Buttons */}
      <div className="flex space-x-2 bg-white rounded-lg shadow-lg p-4">
        <button
          onClick={() => setStatusFilter('all')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            statusFilter === 'all'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          All
        </button>
        <button
          onClick={() => setStatusFilter('completed')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            statusFilter === 'completed'
              ? 'bg-green-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          Completed
        </button>
        <button
          onClick={() => setStatusFilter('failed')}
          className={cn(
            'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
            statusFilter === 'failed'
              ? 'bg-red-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          )}
        >
          Failed
        </button>
      </div>

      {/* Job List */}
      <div className="space-y-4">
        {filteredJobs.map((job) => {
          const isExpanded = expandedJobs.has(job.job_id);
          return (
            <div key={job.job_id} className="bg-white rounded-lg shadow-lg overflow-hidden">
              {/* Job Header */}
              <div
                onClick={() => handleJobClick(job.job_id)}
                className="px-6 py-4 hover:bg-gray-50 transition-colors cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 flex-1 min-w-0">
                    {getStatusIcon(job.status)}
                    
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {job.config?.document_title || 'Untitled Document'}
                      </p>
                      <div className="flex items-center space-x-3 mt-1">
                        <span className={cn(
                          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
                          getStatusColor(job.status)
                        )}>
                          {job.status}
                        </span>
                        <span className="text-xs text-gray-500">
                          {formatRelativeTime(job.created_at)}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2 ml-4">
                    {job.status === 'completed' && job.result && job.result.metrics && (
                      <div className="text-right">
                        <p className="text-sm font-medium text-gray-900">
                          {job.result.metrics.total_steps || 0} steps
                        </p>
                      </div>
                    )}

                    <button
                      onClick={(e) => handleDelete(job.job_id, e)}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                      aria-label="Delete job"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>

                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </div>
              </div>

              {/* Expanded Content - Document Results */}
              {isExpanded && job.status === 'completed' && (
                <div className="border-t border-gray-200 p-6">
                  <DocumentResults jobId={job.job_id} />
                </div>
              )}

              {/* Expanded Content - Failed Job Error */}
              {isExpanded && job.status === 'failed' && (
                <div className="border-t border-gray-200 p-6">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                    <div className="flex items-start space-x-3">
                      <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                      <div>
                        <h4 className="font-semibold text-red-900">Processing Failed</h4>
                        <p className="text-sm text-red-700 mt-1">{job.error || 'Unknown error occurred'}</p>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Load More Button */}
      {hasMore && !loading && filteredJobs.length > 0 && (
        <div className="mt-4 text-center">
          <button
            onClick={loadMore}
            disabled={loadingMore}
            className={cn(
              'px-6 py-3 rounded-lg font-medium transition-colors',
              loadingMore
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            )}
          >
            {loadingMore ? (
              <span className="flex items-center space-x-2">
                <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span>Loading...</span>
              </span>
            ) : (
              `Load More (10 more jobs)`
            )}
          </button>
        </div>
      )}
    </div>
  );
}

