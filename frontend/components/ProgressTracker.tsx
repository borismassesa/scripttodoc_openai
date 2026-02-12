'use client';

import { useEffect, useState, useRef } from 'react';
import { CheckCircle2, Clock, AlertCircle, Download, Loader2, CheckCircle, ArrowRight } from 'lucide-react';
import { getJobStatus, getDocumentDownload, type JobStatus } from '@/lib/api';
import { formatDuration, cn } from '@/lib/utils';

interface ProgressTrackerProps {
  jobId: string;
  onComplete?: (job: JobStatus) => void;
  onAutoNavigate?: () => void;
}

const STAGE_INFO: Record<string, { label: string; progress: number }> = {
  pending: { label: 'Queued', progress: 0 },
  load_transcript: { label: 'Loading Transcript', progress: 10 },
  clean_transcript: { label: 'Cleaning Text', progress: 20 },
  fetch_knowledge: { label: 'Fetching Knowledge', progress: 30 },
  azure_di_analysis: { label: 'Analyzing Document', progress: 35 },
  determine_steps: { label: 'Planning Steps', progress: 40 },
  generate_steps: { label: 'Generating Steps', progress: 60 },
  build_sources: { label: 'Building Citations', progress: 75 },
  validate_steps: { label: 'Validating Quality', progress: 85 },
  create_document: { label: 'Creating Document', progress: 92 },
  upload_document: { label: 'Finalizing', progress: 98 },
  complete: { label: 'Complete', progress: 100 },
};

export default function ProgressTracker({ jobId, onComplete }: ProgressTrackerProps) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState<number>(0);
  const [showTimeline, setShowTimeline] = useState(true); // Timeline expanded by default to show progress
  const isMountedRef = useRef(true);
  const startTimeRef = useRef<Date>(new Date()); // Use component mount time
  const onCompleteRef = useRef<ProgressTrackerProps['onComplete']>(onComplete);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    let timeInterval: NodeJS.Timeout;
    isMountedRef.current = true;

    const pollStatus = async () => {
      try {
        const status = await getJobStatus(jobId);
        if (!isMountedRef.current) return;

        // Debug logging for step generation tracking
        // Debug logging for ALL stage updates (not just generate_steps)
        console.log('[ProgressTracker] 📊 Poll Response:', {
          jobId: jobId.substring(0, 8),
          stage: status.stage,
          current_step: status.current_step,
          total_steps: status.total_steps,
          stage_detail: status.stage_detail,
          progress: status.progress,
          timestamp: new Date().toISOString()
        });

        setJob(prevJob => {
          // Log state changes during step generation
          if (status.stage === 'generate_steps' && status.current_step) {
            if (prevJob?.current_step !== status.current_step) {
              console.log('[ProgressTracker] ✅ Step Changed:', {
                from: prevJob?.current_step,
                to: status.current_step,
                total: status.total_steps
              });
            }
          }
          return status;
        });
        setError(null);

        if (status.status === 'completed') {
          clearInterval(interval);
          clearInterval(timeInterval);
          if (!isMountedRef.current) return;
          if (onCompleteRef.current) onCompleteRef.current(status);

          try {
            const download = await getDocumentDownload(jobId);
            if (!isMountedRef.current) return;
            setDownloadUrl(download.download_url);
          } catch (err) {
            console.error('Failed to get download URL:', err);
          }
        } else if (status.status === 'failed') {
          clearInterval(interval);
          clearInterval(timeInterval);
          if (!isMountedRef.current) return;
          setError(status.error || 'Processing failed');
        }
      } catch (err: any) {
        if (!isMountedRef.current) return;
        if (err?.response?.status === 404) return;
        if (err?.code === 'ECONNABORTED' || err?.message?.includes('timeout')) return;

        console.error('Failed to fetch job status:', err);
        setError(err?.message || 'Failed to check job status');
        clearInterval(interval);
        clearInterval(timeInterval);
      }
    };

    pollStatus();
    interval = setInterval(pollStatus, 2000);

    timeInterval = setInterval(() => {
      const now = new Date();
      const diff = Math.floor((now.getTime() - startTimeRef.current.getTime()) / 1000);
      setElapsedTime(Math.max(0, diff)); // Ensure non-negative
    }, 1000);

    return () => {
      isMountedRef.current = false;
      clearInterval(interval);
      clearInterval(timeInterval);
    };
  }, [jobId]);

  // Debug: Track when current_step changes in the rendered component
  useEffect(() => {
    if (job?.stage === 'generate_steps' && job.current_step) {
      console.log('[ProgressTracker] 🎨 Rendering Step Counter:', {
        current_step: job.current_step,
        total_steps: job.total_steps,
        display: `Generating Step ${job.current_step} of ${job.total_steps}`
      });
    }
  }, [job?.current_step, job?.total_steps, job?.stage]);

  if (!job) {
    return (
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12">
        <div className="flex flex-col items-center justify-center space-y-4">
          <Loader2 className="h-10 w-10 text-blue-600 animate-spin" />
          <span className="text-gray-600 font-medium">Loading job status...</span>
        </div>
      </div>
    );
  }

  const progress = Math.round(job.progress * 100);
  const stageLabel = STAGE_INFO[job.stage]?.label || job.stage;
  const isProcessing = job.status === 'processing';
  const isCompleted = job.status === 'completed';
  const isFailed = job.status === 'failed';

  return (
    <div className="space-y-4">
      {/* Status Card */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Header */}
        <div className={cn(
          'px-6 py-5 border-b border-gray-200',
          isCompleted && 'bg-green-50',
          isFailed && 'bg-red-50',
          isProcessing && 'bg-blue-50'
        )}>
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              {isCompleted && <CheckCircle2 className="h-7 w-7 text-green-600" />}
              {isFailed && <AlertCircle className="h-7 w-7 text-red-600" />}
              {isProcessing && <Loader2 className="h-7 w-7 text-blue-600 animate-spin" />}

              <div>
                <h3 className={cn(
                  'text-lg font-semibold',
                  isCompleted && 'text-green-900',
                  isFailed && 'text-red-900',
                  isProcessing && 'text-blue-900'
                )}>
                  {isCompleted ? 'Document Ready!' : isFailed ? 'Processing Failed' : stageLabel}
                </h3>
                {/* Show stage_detail for ALL stages if no step counter is showing */}
                {job.stage_detail && !job.current_step && (
                  <p className={cn(
                    'text-sm font-medium mt-1',
                    isCompleted && 'text-green-700',
                    isFailed && 'text-red-700',
                    isProcessing && 'text-blue-700'
                  )}>
                    {job.stage_detail}
                  </p>
                )}
              </div>
            </div>

            <div className="text-right">
              <div className={cn(
                'text-3xl font-bold',
                isCompleted && 'text-green-600',
                isFailed && 'text-red-600',
                isProcessing && 'text-blue-600'
              )}>
                {progress}%
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {formatDuration(elapsedTime)}
              </div>
            </div>
          </div>
        </div>

        {/* Step Counter - ALWAYS SHOW at top if available (moved from below progress bar) */}
        {job.current_step && job.total_steps && (
          <div className="px-6 pt-2 pb-0">
            <div className="flex items-center space-x-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-lg px-4 py-3 shadow-sm">
              <div className="flex space-x-1">
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" />
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
              <span className="text-base font-bold text-blue-900">
                Processing Step {job.current_step} of {job.total_steps}
              </span>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        <div className="px-6 py-4">
          <div className="relative w-full h-2.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all duration-500 ease-out rounded-full',
                isCompleted && 'bg-green-500',
                isFailed && 'bg-red-500',
                isProcessing && 'bg-blue-500'
              )}
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Full Progress Timeline - Collapsible to reduce visual clutter */}
        <div className="px-6 pb-6">
          {/* Toggle button */}
          <button
            onClick={() => setShowTimeline(!showTimeline)}
            className="w-full flex items-center justify-between px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900 hover:bg-gray-50 rounded-lg transition-colors"
          >
            <span className="flex items-center space-x-2">
              <span>{showTimeline ? '▲' : '▼'}</span>
              <span>{showTimeline ? 'Hide' : 'Show'} Progress Details</span>
            </span>
            <span className="text-xs text-gray-500">
              {Object.keys(STAGE_INFO).length - 1} stages
            </span>
          </button>

          {showTimeline && (
            <div className="space-y-3 mt-4">
              {/* Phase 1: Setup & Analysis */}
              <div className={cn(
                'p-4 rounded-lg border-2 transition-all',
                progress >= 40 ? 'bg-green-50 border-green-300' : 'bg-blue-50 border-blue-400 shadow-md'
              )}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {progress >= 40 ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                    )}
                    <h4 className={cn(
                      'font-semibold',
                      progress >= 40 ? 'text-green-900' : 'text-blue-900'
                    )}>
                      Phase 1: Setup & Analysis
                    </h4>
                  </div>
                  <span className="text-xs text-gray-600">
                    5 stages
                  </span>
                </div>
                {progress >= 40 && (
                  <p className="text-xs text-green-700 mt-1">All stages complete</p>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {['Queued', 'Loading', 'Cleaning', 'Fetching', 'Analyzing'].map((stage, idx) => (
                    <span key={idx} className={cn(
                      'text-[10px] px-2 py-0.5 rounded-full',
                      progress >= (idx + 1) * 8 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                    )}>
                      {stage}
                    </span>
                  ))}
                </div>
              </div>

              {/* Phase 2: Content Generation */}
              <div className={cn(
                'p-4 rounded-lg border-2 transition-all',
                progress > 75 ? 'bg-green-50 border-green-300' :
                progress >= 40 ? 'bg-blue-50 border-blue-400 shadow-md' :
                'bg-gray-50 border-gray-200'
              )}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {progress > 75 ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : progress >= 40 ? (
                      <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                    <h4 className={cn(
                      'font-semibold',
                      progress > 75 ? 'text-green-900' :
                      progress >= 40 ? 'text-blue-900' :
                      'text-gray-500'
                    )}>
                      Phase 2: Content Generation
                    </h4>
                  </div>
                  <span className="text-xs text-gray-600">
                    3 stages
                  </span>
                </div>
                {job.stage === 'generate_steps' && job.current_step && job.total_steps && (
                  <div className="mt-2 bg-white border-2 border-blue-400 rounded-md px-3 py-2">
                    <p className="text-sm text-blue-900 font-bold">
                      ⏳ Generating step {job.current_step} of {job.total_steps}
                    </p>
                  </div>
                )}
                {job.stage === 'build_sources' && (
                  <div className="mt-2 bg-white border-2 border-blue-400 rounded-md px-3 py-2">
                    <p className="text-sm text-blue-900 font-bold">
                      ⏳ {job.stage_detail || 'Building source citations...'}
                    </p>
                  </div>
                )}
                {job.stage === 'validate_steps' && (
                  <div className="mt-2 bg-white border-2 border-blue-400 rounded-md px-3 py-2">
                    <p className="text-sm text-blue-900 font-bold">
                      ⏳ {job.stage_detail || 'Validating steps...'}
                    </p>
                  </div>
                )}
                {progress > 75 && (
                  <p className="text-xs text-green-700 mt-1">All stages complete</p>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {['Planning', 'Generating', 'Building'].map((stage, idx) => {
                    const stageProgress = 40 + (idx * 12);
                    const isCurrent = job.stage === ['determine_steps', 'generate_steps', 'build_sources'][idx];
                    return (
                      <span key={idx} className={cn(
                        'text-[10px] px-2 py-0.5 rounded-full',
                        progress >= stageProgress + 12 ? 'bg-green-100 text-green-700' :
                        isCurrent ? 'bg-blue-100 text-blue-700 font-semibold ring-2 ring-blue-300' :
                        'bg-gray-100 text-gray-500'
                      )}>
                        {stage}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Phase 3: Quality & Finalization */}
              <div className={cn(
                'p-4 rounded-lg border-2 transition-all',
                isCompleted ? 'bg-green-50 border-green-300' :
                progress >= 75 ? 'bg-blue-50 border-blue-400 shadow-md' :
                'bg-gray-50 border-gray-200'
              )}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {isCompleted ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : progress >= 75 ? (
                      <Loader2 className="h-5 w-5 text-blue-600 animate-spin" />
                    ) : (
                      <div className="h-5 w-5 rounded-full border-2 border-gray-300" />
                    )}
                    <h4 className={cn(
                      'font-semibold',
                      isCompleted ? 'text-green-900' :
                      progress >= 75 ? 'text-blue-900' :
                      'text-gray-500'
                    )}>
                      Phase 3: Quality & Finalization
                    </h4>
                  </div>
                  <span className="text-xs text-gray-600">
                    3 stages
                  </span>
                </div>
                {isCompleted && (
                  <p className="text-xs text-green-700 mt-1">All stages complete</p>
                )}
                <div className="mt-2 flex flex-wrap gap-1">
                  {['Validating', 'Creating', 'Finalizing'].map((stage, idx) => {
                    const stageProgress = 75 + (idx * 8);
                    const isCurrent = job.stage === ['validate_steps', 'create_document', 'upload_document'][idx];
                    return (
                      <span key={idx} className={cn(
                        'text-[10px] px-2 py-0.5 rounded-full',
                        progress >= stageProgress + 8 ? 'bg-green-100 text-green-700' :
                        isCurrent ? 'bg-blue-100 text-blue-700 font-semibold ring-2 ring-blue-300' :
                        'bg-gray-100 text-gray-500'
                      )}>
                        {stage}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Completion Summary - Show when done */}
              {isCompleted && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center space-x-2 text-green-800">
                    <CheckCircle2 className="h-5 w-5" />
                    <span className="font-semibold">All stages completed successfully!</span>
                  </div>
                  <p className="text-xs text-green-700 mt-1">
                    Your document went through {Object.keys(STAGE_INFO).length - 1} processing stages
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Results Card */}
      {isCompleted && job.result && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <div className="bg-green-50 border-b border-green-200 px-6 py-4">
            <h4 className="font-semibold text-green-900 flex items-center">
              <CheckCircle2 className="h-5 w-5 mr-2" />
              Processing Complete
            </h4>
          </div>

          <div className="p-6">
            {downloadUrl && (
              <button
                onClick={() => window.location.href = downloadUrl}
                className="w-full flex items-center justify-center space-x-2 py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                <Download className="h-5 w-5" />
                <span>Download Training Document</span>
              </button>
            )}
          </div>
        </div>
      )}

      {/* Error Card */}
      {isFailed && (
        <div className="bg-white rounded-xl shadow-sm border border-red-200 overflow-hidden">
          <div className="bg-red-50 border-b border-red-200 px-6 py-4">
            <h4 className="font-semibold text-red-900 flex items-center">
              <AlertCircle className="h-5 w-5 mr-2" />
              Processing Failed
            </h4>
          </div>
          <div className="p-6">
            {(() => {
              const errorMessage = error || job.error || 'Unknown error occurred';

              // Check if error message contains structured instructions
              const lines = errorMessage.split('\n').map(l => l.trim()).filter(l => l);
              const hasNumberedSteps = lines.some(l => /^\d+\./.test(l));

              if (hasNumberedSteps) {
                // Parse structured error with instructions
                const mainMessage = lines[0];
                const steps = lines.filter(l => /^\d+\./.test(l));
                const otherLines = lines.filter(l => !(/^\d+\./.test(l)) && l !== mainMessage);

                return (
                  <div className="space-y-4">
                    <p className="text-red-900 font-medium">{mainMessage}</p>

                    {steps.length > 0 && (
                      <div className="bg-red-50 rounded-lg p-4 border border-red-200">
                        <p className="text-sm font-medium text-red-900 mb-3">Please choose one of the following options:</p>
                        <ul className="space-y-2">
                          {steps.map((step, idx) => {
                            const match = step.match(/^(\d+)\.\s*(.+)$/);
                            if (match) {
                              const [_, num, text] = match;
                              return (
                                <li key={idx} className="flex items-start space-x-2">
                                  <span className="flex-shrink-0 w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center text-xs font-bold">
                                    {num}
                                  </span>
                                  <span className="text-sm text-red-800 pt-0.5">{text}</span>
                                </li>
                              );
                            }
                            return null;
                          })}
                        </ul>
                      </div>
                    )}

                    {otherLines.length > 0 && (
                      <div className="text-sm text-red-700 space-y-1">
                        {otherLines.map((line, idx) => (
                          <p key={idx}>{line}</p>
                        ))}
                      </div>
                    )}
                  </div>
                );
              } else {
                // Simple error message
                return (
                  <div>
                    <p className="text-red-900 whitespace-pre-wrap">{errorMessage}</p>
                    <p className="text-sm text-red-700 mt-3">
                      Please try uploading your transcript again after addressing the issue above.
                    </p>
                  </div>
                );
              }
            })()}
          </div>
        </div>
      )}
    </div>
  );
}
