'use client';

import { useState, useCallback, useRef } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, Plus, Link as LinkIcon, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import { generateDocumentTitle } from '@/lib/api';

interface UploadFormProps {
  onUpload: (files: File[], config: UploadConfig) => void;
  isProcessing: boolean;
}

export interface UploadConfig {
  tone: string;
  audience: string;
  document_title: string;
  knowledge_urls: string[];
  min_steps: number;
  target_steps: number;
  max_steps: number;
}

export default function UploadForm({ onUpload, isProcessing }: UploadFormProps) {
  const [files, setFiles] = useState<File[]>([]);
  const [config, setConfig] = useState<UploadConfig>({
    tone: 'Professional',
    audience: 'Technical Users',
    document_title: '',
    knowledge_urls: [],
    min_steps: 5,
    target_steps: 10,
    max_steps: 20,
  });
  const [urlInput, setUrlInput] = useState('');
  const [isGeneratingTitle, setIsGeneratingTitle] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setFiles(prev => [...prev, ...acceptedFiles]);
    }
  }, []);

  const { getRootProps, getInputProps } = useDropzone({
    onDrop,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
    },
    multiple: true,
    disabled: isProcessing,
    noClick: true, // Disable default click behavior
    noKeyboard: false,
    onDragEnter: () => setIsDragActive(true),
    onDragLeave: () => setIsDragActive(false),
    onDropAccepted: () => setIsDragActive(false),
    onDropRejected: () => setIsDragActive(false),
  });

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newFiles = e.target.files;
    if (newFiles && newFiles.length > 0) {
      setFiles(prev => [...prev, ...Array.from(newFiles)]);
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    console.log('Form submitted', { filesCount: files.length, config, isProcessing });

    if (files.length === 0) {
      console.error('No files selected');
      alert('Please select at least one file to upload');
      return;
    }

    if (isProcessing) {
      console.warn('Already processing, ignoring submit');
      return;
    }

    try {
      console.log('Calling onUpload with:', {
        fileNames: files.map(f => f.name),
        config
      });
      onUpload(files, config);
      // Clear files after successful submission
      setFiles([]);
    } catch (error) {
      console.error('Error in handleSubmit:', error);
      alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  };

  const handleRemoveFile = (indexToRemove: number) => {
    setFiles(prev => prev.filter((_, index) => index !== indexToRemove));
  };

  const handleAddUrl = () => {
    const trimmedUrl = urlInput.trim();
    if (trimmedUrl && !config.knowledge_urls.includes(trimmedUrl)) {
      // Basic URL validation
      try {
        new URL(trimmedUrl);
        setConfig({
          ...config,
          knowledge_urls: [...config.knowledge_urls, trimmedUrl],
        });
        setUrlInput('');
      } catch {
        alert('Please enter a valid URL (e.g., https://example.com)');
      }
    }
  };

  const handleRemoveUrl = (urlToRemove: string) => {
    setConfig({
      ...config,
      knowledge_urls: config.knowledge_urls.filter(url => url !== urlToRemove),
    });
  };

  const handleUrlInputKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleAddUrl();
    }
  };

  const handleGenerateTitle = async () => {
    if (files.length === 0) {
      alert('Please upload at least one transcript file first');
      return;
    }

    if (isGeneratingTitle || isProcessing) {
      return;
    }

    try {
      setIsGeneratingTitle(true);

      // Read the first file to extract text
      const firstFile = files[0];
      const text = await firstFile.text();

      if (!text || text.trim().length < 50) {
        alert('The transcript is too short to generate a meaningful title. Please upload a longer transcript.');
        return;
      }

      // Call API to generate title
      const response = await generateDocumentTitle(text);

      if (response.title) {
        setConfig({ ...config, document_title: response.title });
      }
    } catch (error: any) {
      console.error('Failed to generate title:', error);

      // Extract error message from response
      let errorMessage = 'Failed to generate title. Please try again.';

      if (error?.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error?.response?.status === 503) {
        errorMessage = 'AI service is temporarily unavailable. Please ensure Azure OpenAI is configured correctly.';
      } else if (error?.response?.status === 429) {
        errorMessage = 'Rate limit exceeded. Please wait a moment and try again.';
      } else if (error?.message) {
        errorMessage = error.message;
      }

      alert(errorMessage);
    } finally {
      setIsGeneratingTitle(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* File Upload Area */}
      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".txt,.pdf,text/plain,application/pdf"
        onChange={handleFileInputChange}
        disabled={isProcessing}
        multiple
        className="hidden"
      />

      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all',
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400',
          isProcessing && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />

        <div className="space-y-4" onClick={handleBrowseClick}>
          <Upload className="mx-auto h-12 w-12 text-gray-400" />
          <div>
            <p className="text-lg font-medium text-gray-900">
              {isDragActive ? 'Drop transcripts here' : 'Drop transcripts or click to upload'}
            </p>
            <p className="mt-1 text-sm text-gray-500">
              Supports .txt and .pdf files up to 5MB each
            </p>
            {files.length > 0 && (
              <p className="mt-2 text-sm font-medium text-blue-600">
                {files.length} file{files.length !== 1 ? 's' : ''} selected
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Selected Files List */}
      {files.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Selected Files:</h4>
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {files.map((file, index) => (
              <div
                key={`${file.name}-${index}`}
                className="flex items-center justify-between bg-white rounded-lg p-3 border border-gray-200 hover:border-gray-300 transition-colors"
              >
                <div className="flex items-center space-x-3 flex-1 min-w-0">
                  <FileText className="h-6 w-6 text-blue-500 shrink-0" />
                  <div className="text-left min-w-0 flex-1">
                    <p className="font-medium text-gray-900 truncate">{file.name}</p>
                    <p className="text-sm text-gray-500">
                      {(file.size / 1024).toFixed(2)} KB
                    </p>
                  </div>
                </div>
                {!isProcessing && (
                  <button
                    type="button"
                    onClick={() => handleRemoveFile(index)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors shrink-0"
                    aria-label={`Remove ${file.name}`}
                  >
                    <X className="h-5 w-5" />
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Configuration Options */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Document Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
              Document Title
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                id="title"
                value={config.document_title}
                onChange={(e) => setConfig({ ...config, document_title: e.target.value })}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                placeholder="e.g., Azure Deployment Guide"
                disabled={isProcessing}
              />
              <button
                type="button"
                onClick={handleGenerateTitle}
                disabled={files.length === 0 || isGeneratingTitle || isProcessing}
                className={cn(
                  'group font-medium flex items-center gap-2 whitespace-nowrap overflow-hidden relative',
                  'pt-4 pr-8 pb-4 pl-8',
                  files.length > 0 && !isGeneratingTitle && !isProcessing
                    ? 'bg-linear-to-r from-[#FFEBB1] to-[#FFC438] text-orange-900 shadow-orange-500/30 hover:shadow-orange-500/50 transition-all duration-300 shadow-lg'
                    : 'opacity-50 cursor-not-allowed rounded-full bg-gray-300 text-gray-500'
                )}
                style={
                  files.length > 0 && !isGeneratingTitle && !isProcessing
                    ? {
                        boxShadow: '0 15px 33px -12px rgba(255,162,42,0.9), inset 0 4px 6.3px rgba(252,220,134,1), inset 0 -5px 6.3px rgba(255,162,38,1)',
                        borderRadius: '9999px'
                      }
                    : { background: '#d1d5db', border: 'none', boxShadow: 'none', borderRadius: '9999px' }
                }
                title={files.length === 0 ? 'Upload a transcript first' : 'Generate title with AI'}
              >
                <div className="group-hover:translate-y-0 transition-transform duration-300 bg-white/20 absolute top-0 right-0 bottom-0 left-0 translate-y-full"></div>
                {isGeneratingTitle ? (
                  <span className="relative flex items-center gap-2">
                    <svg className="animate-spin h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span className="hidden sm:inline text-sm tracking-tight">Generating...</span>
                  </span>
                ) : (
                  <span className="relative flex items-center gap-2">
                    <Sparkles className="h-4 w-4" />
                    <span className="hidden sm:inline text-sm tracking-tight">AI Generate</span>
                  </span>
                )}
              </button>
            </div>
          </div>

          {/* Auto-detected Steps Info */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Number of Steps
            </label>
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3">
              <div className="flex items-center space-x-2">
                <svg className="h-5 w-5 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                <span className="text-sm font-medium text-blue-900">
                  Automatically detected
                </span>
              </div>
              <p className="text-xs text-blue-700 mt-1">
                AI analyzes your transcript and creates the optimal number of steps based on natural topic boundaries
              </p>
            </div>
          </div>

          {/* Tone */}
          <div>
            <label htmlFor="tone" className="block text-sm font-medium text-gray-700 mb-1">
              Tone
            </label>
            <select
              id="tone"
              value={config.tone}
              onChange={(e) => setConfig({ ...config, tone: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isProcessing}
            >
              <option value="Professional">Professional</option>
              <option value="Technical">Technical</option>
              <option value="Casual">Casual</option>
              <option value="Formal">Formal</option>
            </select>
          </div>

          {/* Audience */}
          <div>
            <label htmlFor="audience" className="block text-sm font-medium text-gray-700 mb-1">
              Target Audience
            </label>
            <select
              id="audience"
              value={config.audience}
              onChange={(e) => setConfig({ ...config, audience: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isProcessing}
            >
              <option value="Technical Users">Technical Users</option>
              <option value="Beginners">Beginners</option>
              <option value="Experts">Experts</option>
              <option value="General Audience">General Audience</option>
            </select>
          </div>
        </div>

        {/* Document Structure Section */}
        <div className="space-y-4 pt-4 border-t border-gray-200">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Document Structure</h3>
            <p className="text-sm text-gray-600 mt-1">
              Control the number of training steps generated in your document
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Minimum Steps */}
            <div>
              <label htmlFor="min-steps" className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Steps
              </label>
              <input
                type="number"
                id="min-steps"
                min={3}
                max={config.target_steps}
                value={config.min_steps}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 3;
                  setConfig({ ...config, min_steps: Math.max(3, Math.min(value, config.target_steps)) });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
              <p className="text-xs text-gray-500 mt-1">At least this many steps</p>
            </div>

            {/* Target Steps */}
            <div>
              <label htmlFor="target-steps" className="block text-sm font-medium text-gray-700 mb-1">
                Target Steps
              </label>
              <input
                type="number"
                id="target-steps"
                min={config.min_steps}
                max={config.max_steps}
                value={config.target_steps}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 10;
                  setConfig({ ...config, target_steps: Math.max(config.min_steps, Math.min(value, config.max_steps)) });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
              <p className="text-xs text-gray-500 mt-1">Ideal number of steps</p>
            </div>

            {/* Maximum Steps */}
            <div>
              <label htmlFor="max-steps" className="block text-sm font-medium text-gray-700 mb-1">
                Maximum Steps
              </label>
              <input
                type="number"
                id="max-steps"
                min={config.target_steps}
                max={50}
                value={config.max_steps}
                onChange={(e) => {
                  const value = parseInt(e.target.value) || 20;
                  setConfig({ ...config, max_steps: Math.max(config.target_steps, Math.min(value, 50)) });
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
              <p className="text-xs text-gray-500 mt-1">Maximum allowed steps</p>
            </div>
          </div>

          {/* Info box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-900">
              <span className="font-medium">💡 Tip:</span> The AI will automatically detect the optimal number of steps
              within your specified range based on the transcript content and conversation flow.
            </p>
          </div>
        </div>

        {/* Knowledge Sources Section */}
        <div className="space-y-4 pt-4 border-t border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Knowledge Sources</h3>
          <p className="text-sm text-gray-600">
            Add additional knowledge sources to enhance the training document generation.
          </p>

          {/* URL Links Input */}
          <div className="space-y-3">
            <label htmlFor="knowledge-urls" className="block text-sm font-medium text-gray-700">
              Reference URLs
            </label>
            <div className="flex gap-2">
              <input
                type="url"
                id="knowledge-urls"
                value={urlInput}
                onChange={(e) => setUrlInput(e.target.value)}
                onKeyPress={handleUrlInputKeyPress}
                placeholder="https://example.com/documentation"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={isProcessing}
              />
              <button
                type="button"
                onClick={handleAddUrl}
                disabled={!urlInput.trim() || isProcessing}
                className={cn(
                  'px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2',
                  urlInput.trim() && !isProcessing
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                )}
              >
                <Plus className="h-4 w-4" />
                Add
              </button>
            </div>

            {/* URL List */}
            {config.knowledge_urls.length > 0 && (
              <div className="space-y-2">
                {config.knowledge_urls.map((url, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between bg-gray-50 rounded-lg p-3 border border-gray-200"
                  >
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      <LinkIcon className="h-4 w-4 text-blue-500 shrink-0" />
                      <a
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:text-blue-800 truncate"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {url}
                      </a>
                    </div>
                    {!isProcessing && (
                      <button
                        type="button"
                        onClick={() => handleRemoveUrl(url)}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors shrink-0"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={files.length === 0 || isProcessing}
        className={cn(
          'w-full py-3 px-4 rounded-lg font-medium text-white transition-all',
          files.length > 0 && !isProcessing
            ? 'bg-blue-600 hover:bg-blue-700 active:scale-[0.98]'
            : 'bg-gray-300 cursor-not-allowed'
        )}
      >
        {isProcessing ? (
          <span className="flex items-center justify-center">
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Processing...
          </span>
        ) : files.length > 1 ? (
          `Generate ${files.length} Training Documents`
        ) : (
          'Generate Training Document'
        )}
      </button>
    </form>
  );
}

