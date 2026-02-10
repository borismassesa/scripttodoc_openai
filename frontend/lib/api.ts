/**
 * API client for ScriptToDoc backend
 */

import axios from 'axios';

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout (increased for Cosmos DB queries)
});

/**
 * Set authentication token for API requests
 */
export function setAuthToken(token: string | null) {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete apiClient.defaults.headers.common['Authorization'];
  }
}

// Add request interceptor for debugging and auth
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);

    // Get token from localStorage if not already set
    if (typeof window !== 'undefined' && !config.headers['Authorization']) {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers['Authorization'] = `Bearer ${token}`;
      }
    }

    return config;
  },
  (error) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle canceled/aborted requests silently - don't log as errors
    const isCanceled = 
      error.code === 'ECONNABORTED' || 
      error.message === 'canceled' ||
      error.message?.includes('timeout') ||
      error.message?.includes('aborted') ||
      error.name === 'AbortError' ||
      error.name === 'CanceledError' ||
      error.message?.includes('canceled') ||
      error.code === 'ERR_CANCELED';
    
    if (isCanceled) {
      // Request was cancelled/aborted - this is expected, don't log as error
      error.isCanceled = true;
      // Suppress console error for canceled requests
      error.silent = true;
      return Promise.reject(error);
    }
    
    if (error.code === 'ECONNREFUSED' || error.message === 'Network Error') {
      console.error(
        `[API] Connection refused. Is the backend running at ${API_BASE_URL}?`
      );
      error.message = `Cannot connect to backend API at ${API_BASE_URL}. Please ensure the backend server is running.`;
    } else if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;
      
      // Don't log 404s as errors for job status (job might not exist yet)
      if (status === 404 && error.config?.url?.includes('/api/status/')) {
        // Job not found - this is expected for newly created jobs
        error.isNotFound = true;
        error.message = data?.detail || 'Job not found';
      } else {
        console.error(`[API] ${status}:`, data);
        error.message = data?.detail || data?.message || `Request failed with status ${status}`;
      }
    } else {
      // Only log if not a canceled/aborted request
      if (!error.isCanceled) {
        console.error('[API] Error:', error.message);
      }
    }
    return Promise.reject(error);
  }
);

export interface ProcessConfig {
  tone: string;
  audience: string;
  document_title?: string;
  include_statistics: boolean;
  knowledge_urls?: string[];
  min_steps?: number;
  target_steps?: number;
  max_steps?: number;
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  progress: number;
  stage: string;
  current_step?: number;
  total_steps?: number;
  stage_detail?: string;
  created_at: string;
  updated_at: string;
  config?: ProcessConfig;
  result?: {
    document_blob_path: string;
    filename: string;
    metrics: {
      total_steps: number;
      average_confidence: number;
      high_confidence_steps: number;
      processing_time: number;
      input_tokens?: number;
      output_tokens?: number;
      total_tokens?: number;
    };
  };
  error?: string;
}

export interface ProcessResponse {
  job_id: string;
  status: string;
  message: string;
}

export interface DocumentDownload {
  download_url: string;
  expires_in: number;
  filename: string;
  format: 'docx' | 'pdf' | 'pptx';
}

/**
 * Upload transcript and start processing
 */
export async function uploadTranscript(
  file: File,
  config: Partial<ProcessConfig> = {}
): Promise<ProcessResponse> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('tone', config.tone || 'Professional');
  formData.append('audience', config.audience || 'Technical Users');

  // Step count configuration - user can control min/target/max
  if (config.min_steps !== undefined) {
    formData.append('min_steps', config.min_steps.toString());
  }
  if (config.target_steps !== undefined) {
    formData.append('target_steps', config.target_steps.toString());
  }
  if (config.max_steps !== undefined) {
    formData.append('max_steps', config.max_steps.toString());
  }

  if (config.document_title) {
    formData.append('document_title', config.document_title);
  }

  formData.append('include_statistics', String(config.include_statistics ?? true));

  // Add knowledge URLs
  if (config.knowledge_urls && config.knowledge_urls.length > 0) {
    formData.append('knowledge_urls', JSON.stringify(config.knowledge_urls));
  }

  const response = await apiClient.post<ProcessResponse>('/api/process', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 120000, // 120 seconds timeout for file uploads (backend processes synchronously)
  });

  return response.data;
}

/**
 * Get job status
 */
export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const response = await apiClient.get<JobStatus>(`/api/status/${jobId}`, {
    headers: {
      'Cache-Control': 'no-cache, no-store, must-revalidate',
      'Pragma': 'no-cache',
      'Expires': '0'
    }
  });
  return response.data;
}

/**
 * Get all jobs for user
 */
export async function getAllJobs(limit: number = 10, signal?: AbortSignal): Promise<JobStatus[]> {
  const response = await apiClient.get<JobStatus[]>('/api/jobs', {
    params: { limit },
    signal, // Support AbortSignal for cancellation
  });
  return response.data;
}

/**
 * Get document download URL
 */
export async function getDocumentDownload(
  jobId: string,
  format: 'docx' | 'pdf' | 'pptx' = 'docx'
): Promise<DocumentDownload> {
  const response = await apiClient.get<DocumentDownload>(
    `/api/documents/${jobId}`,
    {
      params: { format },
      timeout: 60000, // 60 seconds timeout (longer for conversion + SAS URL generation)
    }
  );
  return response.data;
}

/**
 * Delete job and document
 */
export async function deleteJob(jobId: string): Promise<void> {
  await apiClient.delete(`/api/documents/${jobId}`);
}

/**
 * Generate document title from transcript text using AI
 */
export async function generateDocumentTitle(text: string): Promise<{ title: string }> {
  const formData = new FormData();
  formData.append('text', text);

  const response = await apiClient.post<{ title: string }>('/api/generate-title', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 20000, // 20 seconds timeout
  });

  return response.data;
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; timestamp: string }> {
  const response = await apiClient.get('/health');
  return response.data;
}

export default apiClient;
