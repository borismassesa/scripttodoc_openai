'use client';

import { useEffect, useState } from 'react';
import { FileText, ExternalLink, CheckCircle2, ArrowLeft, Clock, FileCheck, Download, Coins, ArrowUpCircle, ArrowDownCircle } from 'lucide-react';
import { getJobStatus, getDocumentDownload, type JobStatus, API_BASE_URL } from '@/lib/api';
import { formatDuration, getConfidenceColor, cn } from '@/lib/utils';
import FormatSelector, { type DocumentFormat, getFormatLabel } from './FormatSelector';

interface DocumentResultsProps {
  jobId: string;
  onBack?: () => void;
  showBackButton?: boolean;
}

// Helper to format large numbers with commas
const formatNumber = (num: number): string => {
  return num.toLocaleString('en-US');
};

// Helper to calculate cost (example rates - adjust as needed)
const calculateCost = (inputTokens: number, outputTokens: number): string => {
  const INPUT_COST_PER_1K = 0.003;  // $0.003 per 1K input tokens
  const OUTPUT_COST_PER_1K = 0.015; // $0.015 per 1K output tokens

  const inputCost = (inputTokens / 1000) * INPUT_COST_PER_1K;
  const outputCost = (outputTokens / 1000) * OUTPUT_COST_PER_1K;
  const totalCost = inputCost + outputCost;

  return `$${totalCost.toFixed(4)}`;
};

export default function DocumentResults({ jobId, onBack, showBackButton = false }: DocumentResultsProps) {
  const [job, setJob] = useState<JobStatus | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [downloadLoading, setDownloadLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<DocumentFormat>('docx');

  useEffect(() => {
    const loadJob = async () => {
      try {
        setLoading(true);
        const status = await getJobStatus(jobId);
        setJob(status);

        if (status.status === 'completed') {
          try {
            const download = await getDocumentDownload(jobId);
            setDownloadUrl(download.download_url);
          } catch (err) {
            console.error('Failed to get download URL:', err);
          }
        }
        setError(null);
      } catch (err: any) {
        console.error('Failed to load job:', err);
        setError(err?.message || 'Failed to load document results');
      } finally {
        setLoading(false);
      }
    };

    loadJob();
  }, [jobId]);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-center space-x-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="text-gray-600">Loading document results...</span>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error || 'Document not found'}</p>
          {onBack && (
            <button
              onClick={onBack}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Go Back
            </button>
          )}
        </div>
      </div>
    );
  }

  if (job.status !== 'completed') {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="text-center">
          <p className="text-gray-600 mb-4">
            Document is not ready yet. Status: {job.status}
          </p>
          {onBack && (
            <button
              onClick={onBack}
              className="text-blue-600 hover:text-blue-700 font-medium"
            >
              ← Go Back
            </button>
          )}
        </div>
      </div>
    );
  }

  const metrics = {
    total_steps: 0,
    average_confidence: 0,
    high_confidence_steps: 0,
    processing_time: 0,
    input_tokens: 0,
    output_tokens: 0,
    total_tokens: 0,
    ...job.result?.metrics,
  };

  const filename = job.result?.filename || 'training_document.docx';

  // Token metrics (with fallback values if not provided by backend)
  const inputTokens = metrics.input_tokens || 0;
  const outputTokens = metrics.output_tokens || 0;
  const totalTokens = metrics.total_tokens || (inputTokens + outputTokens);
  const cost = calculateCost(inputTokens, outputTokens);

  // Generate Office Online preview URL (only for HTTP/HTTPS URLs, not local file:// URLs)
  const isLocalFile = downloadUrl?.startsWith('file://');
  const officeOnlineUrl = downloadUrl && !isLocalFile
    ? `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(downloadUrl)}`
    : null;

  // Handle format download
  const handleFormatDownload = async (format: DocumentFormat) => {
    try {
      setDownloadLoading(true);
      setError(null);

      // Get download URL for selected format
      const download = await getDocumentDownload(jobId, format);

      // Check if it's a local API URL (starts with /api/)
      const isLocalApiUrl = download.download_url.startsWith('/api/');

      if (isLocalApiUrl) {
        // For local API URLs, fetch with authentication headers
        const token = localStorage.getItem('auth_token');
        const fullUrl = `${API_BASE_URL}${download.download_url}`;
        const response = await fetch(fullUrl, {
          headers: token ? { 'Authorization': `Bearer ${token}` } : {}
        });

        if (!response.ok) {
          throw new Error(`Download failed: ${response.statusText}`);
        }

        // Create blob from response
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);

        // Trigger download
        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = download.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up blob URL
        window.URL.revokeObjectURL(blobUrl);
      } else {
        // For external URLs (Azure SAS URLs), use direct link
        const link = document.createElement('a');
        link.href = download.download_url;
        link.download = download.filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      }

    } catch (err: any) {
      console.error('Download failed:', err);
      setError(err?.message || 'Failed to download document');
    } finally {
      setDownloadLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 md:p-8">
        {/* Back button */}
        {showBackButton && onBack && (
          <button
            onClick={onBack}
            className="mb-6 flex items-center space-x-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="text-sm font-medium">Back to Jobs</span>
          </button>
        )}

        {/* Success Message */}
        <div className="flex items-start space-x-4">
          <div className="shrink-0">
            <div className="h-12 w-12 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle2 className="h-7 w-7 text-green-600" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl md:text-2xl font-semibold text-gray-900 mb-2">
              Document Ready
            </h1>
            <p className="text-gray-600 text-sm mb-4">
              Your training document has been generated and is ready to download
            </p>

            {/* Document Info */}
            <div className="mt-4 pt-4 border-t border-gray-200">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center space-x-3">
                  <FileText className="h-5 w-5 text-gray-400 shrink-0" />
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {job.config?.document_title || 'Training Document'}
                    </p>
                    <p className="text-xs text-gray-500 mt-0.5 truncate">
                      {filename}
                    </p>
                  </div>
                </div>
                <div className="text-left sm:text-right shrink-0">
                  <p className="text-xs text-gray-500">Generated</p>
                  <p className="text-sm text-gray-700">
                    {new Date(job.created_at).toLocaleDateString('en-US', {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric'
                    })}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 md:gap-4">
        {/* Steps */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="h-8 w-8 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
              <FileCheck className="h-4 w-4 text-blue-600" />
            </div>
          </div>
          <p className="text-xl md:text-2xl font-semibold text-gray-900 truncate">
            {metrics.total_steps || 0}
          </p>
          <p className="text-xs text-gray-600 mt-1">Steps</p>
        </div>

        {/* Processing Time */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="h-8 w-8 rounded-lg bg-purple-50 flex items-center justify-center shrink-0">
              <Clock className="h-4 w-4 text-purple-600" />
            </div>
          </div>
          <p className="text-xl md:text-2xl font-semibold text-gray-900 truncate">
            {formatDuration(metrics.processing_time || 0)}
          </p>
          <p className="text-xs text-gray-600 mt-1">Time</p>
        </div>

        {/* Input Tokens */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="h-8 w-8 rounded-lg bg-green-50 flex items-center justify-center shrink-0">
              <ArrowDownCircle className="h-4 w-4 text-green-600" />
            </div>
          </div>
          <p className="text-xl md:text-2xl font-semibold text-gray-900 truncate">
            {inputTokens > 0 ? formatNumber(inputTokens) : '—'}
          </p>
          <p className="text-xs text-gray-600 mt-1">Input Tokens</p>
        </div>

        {/* Output Tokens */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="h-8 w-8 rounded-lg bg-orange-50 flex items-center justify-center shrink-0">
              <ArrowUpCircle className="h-4 w-4 text-orange-600" />
            </div>
          </div>
          <p className="text-xl md:text-2xl font-semibold text-gray-900 truncate">
            {outputTokens > 0 ? formatNumber(outputTokens) : '—'}
          </p>
          <p className="text-xs text-gray-600 mt-1">Output Tokens</p>
        </div>

        {/* Cost */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="h-8 w-8 rounded-lg bg-emerald-50 flex items-center justify-center shrink-0">
              <Coins className="h-4 w-4 text-emerald-600" />
            </div>
          </div>
          <p className="text-xl md:text-2xl font-semibold text-gray-900 truncate">
            {(inputTokens > 0 || outputTokens > 0) ? cost : '—'}
          </p>
          <p className="text-xs text-gray-600 mt-1">Est. Cost</p>
        </div>
      </div>

      {/* Download Section */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Download Options</h2>

        <FormatSelector
          onFormatChange={setSelectedFormat}
          selectedFormat={selectedFormat}
          loading={downloadLoading}
        />

        {error && (
          <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-3">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Action Buttons Row */}
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="flex flex-col sm:flex-row gap-3">
            {/* Download Button */}
            <button
              onClick={() => handleFormatDownload(selectedFormat)}
              disabled={downloadLoading}
              className="flex-1 inline-flex items-center justify-center space-x-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 disabled:cursor-not-allowed text-white rounded-lg text-sm font-medium transition-colors"
            >
              <Download className="h-4 w-4" />
              <span>{downloadLoading ? 'Downloading...' : `Download ${getFormatLabel(selectedFormat)}`}</span>
            </button>

            {/* Preview Button */}
            {downloadUrl && officeOnlineUrl && selectedFormat === 'docx' && (
              <a
                href={officeOnlineUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 inline-flex items-center justify-center space-x-2 px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 transition-colors"
              >
                <ExternalLink className="h-4 w-4" />
                <span>Preview in Browser</span>
              </a>
            )}
          </div>
        </div>
      </div>

      {/* Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <div className="shrink-0">
            <div className="h-8 w-8 rounded-lg bg-blue-100 flex items-center justify-center">
              <FileText className="h-4 w-4 text-blue-600" />
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm text-blue-900">
              <span className="font-medium">About this document:</span> Professional Word format with step-by-step instructions,
              formatted content, and AI-generated training material.
              {isLocalFile ? (
                <> Download the file and open it in Microsoft Word to view and edit.</>
              ) : (
                <> Edit in Microsoft Word or preview online.</>
              )}
            </p>
          </div>
        </div>
      </div>

      {/* Token Info Message (shown when tokens are not available) */}
      {inputTokens === 0 && outputTokens === 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <div className="shrink-0">
              <div className="h-8 w-8 rounded-lg bg-amber-100 flex items-center justify-center">
                <Coins className="h-4 w-4 text-amber-600" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-amber-900">
                <span className="font-medium">Token metrics unavailable:</span> The backend needs to return <code className="bg-amber-100 px-1 py-0.5 rounded text-xs">input_tokens</code>, <code className="bg-amber-100 px-1 py-0.5 rounded text-xs">output_tokens</code>, and <code className="bg-amber-100 px-1 py-0.5 rounded text-xs">total_tokens</code> in the job metrics to display cost information.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
