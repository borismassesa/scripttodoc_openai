'use client';

import { Download, FileText, Presentation } from 'lucide-react';
import { useState } from 'react';

export type DocumentFormat = 'docx' | 'pdf' | 'pptx';

interface FormatSelectorProps {
  onFormatChange?: (format: DocumentFormat) => void;
  selectedFormat?: DocumentFormat;
  loading?: boolean;
}

const FORMAT_OPTIONS = [
  {
    value: 'docx' as const,
    label: 'Word Document',
    ext: '.docx',
    icon: FileText,
  },
  {
    value: 'pdf' as const,
    label: 'PDF Document',
    ext: '.pdf',
    icon: FileText,
  },
  {
    value: 'pptx' as const,
    label: 'PowerPoint',
    ext: '.pptx',
    icon: Presentation,
  },
];

export default function FormatSelector({ onFormatChange, selectedFormat: externalFormat, loading = false }: FormatSelectorProps) {
  const [internalFormat, setInternalFormat] = useState<DocumentFormat>('docx');
  const selectedFormat = externalFormat || internalFormat;

  const handleFormatChange = (format: DocumentFormat) => {
    setInternalFormat(format);
    onFormatChange?.(format);
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-3">
        Select Format
      </label>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {FORMAT_OPTIONS.map((option) => {
          const Icon = option.icon;
          const isSelected = selectedFormat === option.value;
          return (
            <button
              key={option.value}
              onClick={() => handleFormatChange(option.value)}
              disabled={loading}
              className={`
                relative flex items-start p-4 border-2 rounded-lg transition-all
                ${isSelected
                  ? 'border-blue-600 bg-blue-50'
                  : 'border-gray-200 bg-white hover:border-gray-300'
                }
                ${loading ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
              `}
            >
              <div className="flex items-start space-x-3 w-full">
                <div className={`shrink-0 h-10 w-10 rounded-lg flex items-center justify-center ${
                  isSelected ? 'bg-blue-100' : 'bg-gray-100'
                }`}>
                  <Icon className={`h-5 w-5 ${isSelected ? 'text-blue-600' : 'text-gray-600'}`} />
                </div>
                <div className="flex-1 text-left">
                  <div className="flex items-center justify-between">
                    <p className={`text-sm font-medium ${isSelected ? 'text-blue-900' : 'text-gray-900'}`}>
                      {option.label}
                    </p>
                    {isSelected && (
                      <div className="shrink-0 h-5 w-5 rounded-full bg-blue-600 flex items-center justify-center">
                        <svg className="h-3 w-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                          <path d="M10 3L4.5 8.5 2 6" stroke="white" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-gray-500 mt-1">{option.ext}</p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// Helper to get format label
export function getFormatLabel(format: DocumentFormat): string {
  const option = FORMAT_OPTIONS.find(opt => opt.value === format);
  return option?.label || 'Document';
}
