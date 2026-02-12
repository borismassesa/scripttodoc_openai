'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { FileText, Clock } from 'lucide-react';
import { getAllJobs, type JobStatus } from '@/lib/api';
import ProgressTracker from '@/components/ProgressTracker';
import EmptyState from '@/components/EmptyState';
import Celebration from '@/components/Celebration';
import { formatRelativeTime, cn } from '@/lib/utils';

interface ActiveJobsProps {
  refreshTrigger?: number;
  onJobComplete?: (job: JobStatus) => void;
  onNavigateToCreate?: () => void;
  justUploadedJobId?: string | null;
  onJobAppeared?: () => void;
}

export default function ActiveJobs({ refreshTrigger, onJobComplete, onNavigateToCreate, justUploadedJobId, onJobAppeared }: ActiveJobsProps) {
  const [activeJobs, setActiveJobs] = useState<JobStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [celebrateJob, setCelebrateJob] = useState<JobStatus | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isMountedRef = useRef(true);
  const isFetchingRef = useRef(false);
  const previousActiveCountRef = useRef<number>(0);

  // Track which jobs we've already celebrated (to avoid showing confetti multiple times)
  const celebratedJobsRef = useRef<Set<string>>(new Set());

  // Track previous job statuses to detect state transitions
  const previousJobStatusesRef = useRef<Map<string, string>>(new Map());

  // Track completion timestamps to keep completed jobs visible for a few seconds
  const completionTimestampsRef = useRef<Map<string, number>>(new Map());

  const fetchActiveJobs = useCallback(async (showLoading = false) => {
    console.log('[ActiveJobs] fetchActiveJobs called', { showLoading, isMounted: isMountedRef.current });
    
    // Only cancel previous request if it's still pending AND we're doing a forced refresh
    // Don't cancel on every poll - let requests complete naturally
    if (showLoading && abortControllerRef.current) {
      console.log('[ActiveJobs] Canceling previous request for forced refresh');
      abortControllerRef.current.abort();
    }

    // Create new abort controller for this request
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      if (showLoading) {
        console.log('[ActiveJobs] Setting loading to true');
        setLoading(true);
      }
      
      console.log('[ActiveJobs] Calling getAllJobs...');
      const allJobs = await getAllJobs(50, signal);
      console.log('[ActiveJobs] getAllJobs response:', {
        count: allJobs.length,
        jobs: allJobs.map(j => ({ id: j.job_id, status: j.status }))
      });

      if (!isMountedRef.current || signal.aborted) {
        console.log('[ActiveJobs] Component unmounted or request aborted, skipping update');
        // Still clear loading state even if aborted
        if (isMountedRef.current) {
          setLoading(false);
        }
        return;
      }

      // Detect jobs that JUST transitioned from processing/queued to completed
      const now = Date.now();
      allJobs.forEach((job) => {
        const previousStatus = previousJobStatusesRef.current.get(job.job_id);

        // Track when job completes (for keeping it visible)
        if (
          job.status === 'completed' &&
          previousStatus === 'processing' &&
          !completionTimestampsRef.current.has(job.job_id)
        ) {
          console.log(`[ActiveJobs] Job completed, marking timestamp:`, job.job_id);
          completionTimestampsRef.current.set(job.job_id, now);
        }

        // Only celebrate if:
        // 1. Job is now completed
        // 2. Previous status was processing or queued (transition detected)
        // 3. Haven't celebrated this job yet
        if (
          job.status === 'completed' &&
          (previousStatus === 'processing' || previousStatus === 'queued') &&
          !celebratedJobsRef.current.has(job.job_id)
        ) {
          console.log(`[ActiveJobs] 🎉 Job transitioned ${previousStatus} → completed, showing confetti:`, job.job_id);
          celebratedJobsRef.current.add(job.job_id);
          setCelebrateJob(job);
        }
      });

      // Filter for active jobs:
      // 1. Queued or processing jobs (always show)
      // 2. Completed jobs that finished within last 5 seconds (keep visible for celebration)
      const COMPLETION_VISIBILITY_MS = 5000; // Keep completed jobs visible for 5 seconds
      const active = allJobs.filter((job) => {
        if (job.status === 'queued' || job.status === 'processing') {
          return true; // Always show in-progress jobs
        }

        if (job.status === 'completed') {
          const completedAt = completionTimestampsRef.current.get(job.job_id);
          if (completedAt) {
            const elapsed = now - completedAt;
            const shouldKeepVisible = elapsed < COMPLETION_VISIBILITY_MS;

            if (!shouldKeepVisible) {
              console.log(`[ActiveJobs] Removing completed job from active view (${elapsed}ms elapsed):`, job.job_id);
              // Clean up timestamp tracking
              completionTimestampsRef.current.delete(job.job_id);
            }

            return shouldKeepVisible; // Keep visible for 5 seconds after completion
          }
        }

        return false; // Failed jobs, etc. go to History immediately
      });

      // Update previous statuses for next poll
      const newStatuses = new Map<string, string>();
      allJobs.forEach((job) => {
        newStatuses.set(job.job_id, job.status);
      });
      previousJobStatusesRef.current = newStatuses;

      console.log(`[ActiveJobs] Filtered: ${allJobs.length} total jobs, ${active.length} active (queued/processing)`);
      console.log('[ActiveJobs] Active jobs:', active.map(j => ({ id: j.job_id, status: j.status })));

      setActiveJobs(active);
      setError(null);
      console.log('[ActiveJobs] State updated successfully');
    } catch (err: any) {
      // Silently handle timeout and canceled requests - these are expected
      const isCanceled = 
        signal.aborted ||
        err?.code === 'ECONNABORTED' || 
        err?.message === 'canceled' ||
        err?.message?.includes('timeout') ||
        err?.message?.includes('aborted') ||
        err?.name === 'AbortError' ||
        err?.name === 'CanceledError' ||
        err?.isCanceled ||
        err?.code === 'ERR_CANCELED';
      
      if (isCanceled) {
        // Silently ignore canceled requests - don't log as error
        // Still clear loading state - don't prevent future requests
        if (isMountedRef.current) {
          setLoading(false);
        }
        // Don't set error state for canceled requests - they'll retry automatically
        return;
      }
      
      // Only log non-canceled errors
      console.error('[ActiveJobs] Error in fetchActiveJobs:', err);
      
      if (!isMountedRef.current) {
        console.log('[ActiveJobs] Component unmounted, not setting error');
        return;
      }
      
      setError(err?.message || 'Failed to load active jobs');
    } finally {
      if (isMountedRef.current && !signal.aborted) {
        console.log('[ActiveJobs] Setting loading to false');
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    console.log('[ActiveJobs] Component mounted/updated', { refreshTrigger });
    isMountedRef.current = true;

    // Initial fetch with loading state
    console.log('[ActiveJobs] Starting initial fetch');
    fetchActiveJobs(true);

    // ⭐ FIXED: Poll every 5 seconds (increased from 2s to avoid canceling requests too quickly)
    // Only start new request if previous one completed or was canceled
    const interval = setInterval(() => {
      if (isMountedRef.current && !isFetchingRef.current) {
        isFetchingRef.current = true;
        fetchActiveJobs(false)
          .catch((err) => {
            // Silently handle canceled errors during polling
            if (
              err?.isCanceled ||
              err?.name === 'CanceledError' ||
              err?.message === 'canceled'
            ) {
              // Expected - request was canceled, ignore
              return;
            }
            // Log unexpected errors
            console.error('[ActiveJobs] Polling error:', err);
          })
          .finally(() => {
            isFetchingRef.current = false;
          });
      }
    }, 5000);

    return () => {
      console.log('[ActiveJobs] Component unmounting, cleaning up');
      isMountedRef.current = false;
      clearInterval(interval);
      // Abort any pending requests, but catch the error silently
      if (abortControllerRef.current) {
        try {
          abortControllerRef.current.abort();
        } catch (e) {
          // Silently ignore abort errors during cleanup
        }
      }
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [refreshTrigger]);

  // Detect when the uploaded job appears in the list
  useEffect(() => {
    if (justUploadedJobId && activeJobs.some(job => job.job_id === justUploadedJobId)) {
      console.log('[ActiveJobs] Uploaded job appeared in list:', justUploadedJobId);
      if (onJobAppeared) {
        onJobAppeared();
      }
    }
  }, [justUploadedJobId, activeJobs, onJobAppeared]);

  // Track previous active count for reference (no auto-switch)
  useEffect(() => {
    // Update the previous count
    previousActiveCountRef.current = activeJobs.length;
  }, [activeJobs.length]);

  // Debug logging for render
  console.log('[ActiveJobs] Render:', { 
    loading, 
    error, 
    activeJobsCount: activeJobs.length, 
    activeJobs: activeJobs.map(j => ({ id: j.job_id, status: j.status, stage: j.stage }))
  });

  if (loading && activeJobs.length === 0 && !justUploadedJobId) {
    console.log('[ActiveJobs] Rendering loading state');
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="animate-pulse space-y-4">
          {[...Array(2)].map((_, i) => (
            <div key={i} className="h-32 bg-gray-200 rounded-lg"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error && activeJobs.length === 0) {
    console.log('[ActiveJobs] Rendering error state:', error);
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <div className="text-red-600 space-y-2">
          <p className="font-semibold">Error loading active jobs</p>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => {
              console.log('[ActiveJobs] Retry button clicked');
              fetchActiveJobs(true);
            }}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Show optimistic placeholder for just-uploaded job if it hasn't appeared yet
  const showPlaceholder = justUploadedJobId && !activeJobs.some(j => j.job_id === justUploadedJobId);
  const jobsToDisplay = activeJobs.length === 0 && !showPlaceholder;

  if (jobsToDisplay) {
    console.log('[ActiveJobs] Rendering empty state (no active jobs)');
    return (
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        <EmptyState
          variant="no-active"
          title="No Active Jobs"
          description="All jobs have completed! Switch to the History tab to view and download your documents, or create a new document to get started."
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Show count of active jobs */}
      {(activeJobs.length > 0 || showPlaceholder) && (() => {
        const processingCount = activeJobs.filter(j => j.status === 'processing' || j.status === 'queued').length + (showPlaceholder ? 1 : 0);
        const completedCount = activeJobs.filter(j => j.status === 'completed').length;

        return (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-blue-600" />
              <p className="text-sm font-medium text-blue-900">
                {processingCount > 0 && `Processing ${processingCount} job${processingCount !== 1 ? 's' : ''}`}
                {processingCount > 0 && completedCount > 0 && ' • '}
                {completedCount > 0 && `${completedCount} completed (will move to History in 5s)`}
              </p>
            </div>
            <p className="text-xs text-blue-700 mt-1">
              Jobs will continue processing even if you switch tabs or start new uploads.
            </p>
          </div>
        );
      })()}

      {/* Show placeholder for just-uploaded job */}
      {showPlaceholder && (
        <div className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Job Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="h-5 w-5 text-blue-500" />
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">
                    Processing...
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Just uploaded
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                  queued
                </span>
              </div>
            </div>
          </div>

          {/* Progress Tracker */}
          <div className="p-6">
            <ProgressTracker
              jobId={justUploadedJobId}
              onComplete={(completedJob) => {
                if (onJobComplete) {
                  onJobComplete(completedJob);
                }
                fetchActiveJobs(false);
              }}
              onAutoNavigate={onNavigateToCreate}
            />
          </div>
        </div>
      )}

      {activeJobs.map((job) => (
        <div key={job.job_id} className="bg-white rounded-lg shadow-lg overflow-hidden">
          {/* Job Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <FileText className="h-5 w-5 text-blue-500" />
                <div>
                  <h3 className="text-sm font-semibold text-gray-900">
                    {job.config?.document_title || 'Untitled Document'}
                  </h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Started {formatRelativeTime(job.created_at)}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span
                  className={cn(
                    'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
                    job.status === 'completed'
                      ? 'bg-green-100 text-green-800'
                      : job.status === 'processing'
                      ? 'bg-blue-100 text-blue-800'
                      : 'bg-gray-100 text-gray-800'
                  )}
                >
                  {job.status}
                </span>
              </div>
            </div>
          </div>

          {/* Progress Tracker */}
          <div className="p-6">
            <ProgressTracker
              jobId={job.job_id}
              onComplete={(completedJob) => {
                // Don't trigger celebration here - it's already handled by the polling detection above
                // This prevents duplicate confetti animations
                if (onJobComplete) {
                  onJobComplete(completedJob);
                }
                // Refresh the list without showing loading state
                fetchActiveJobs(false);
              }}
              onAutoNavigate={onNavigateToCreate}
            />
          </div>
        </div>
      ))}

      {/* Celebration Overlay */}
      {celebrateJob && (
        <Celebration
          documentTitle={celebrateJob.config?.document_title}
          onClose={() => setCelebrateJob(null)}
        />
      )}
    </div>
  );
}

