'use client';

import { LucideIcon, FileText, Clock, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  variant: 'no-active' | 'no-history' | 'processing';
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export default function EmptyState({
  variant,
  title,
  description,
  icon: Icon,
  action,
  className
}: EmptyStateProps) {
  return (
    <div className={cn('text-center py-16 px-6', className)}>
      {/* Modern Illustration */}
      <div className="relative mx-auto mb-8 w-48 h-48">
        {variant === 'processing' && <ProcessingIllustration />}
        {variant === 'no-active' && <NoActiveIllustration />}
        {variant === 'no-history' && <NoHistoryIllustration />}
      </div>

      {/* Content */}
      <div className="max-w-md mx-auto space-y-3">
        <h3 className="text-2xl font-bold text-gray-900 tracking-tight">
          {title}
        </h3>
        <p className="text-base text-gray-600 leading-relaxed">
          {description}
        </p>

        {/* Optional Action Button */}
        {action && (
          <div className="pt-4">
            <button
              onClick={action.onClick}
              className="inline-flex items-center px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-all hover:scale-105 active:scale-95 shadow-lg hover:shadow-xl"
            >
              {action.label}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Clean, modern processing animation
function ProcessingIllustration() {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {/* Outer rotating ring */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="w-40 h-40 rounded-full border-4 border-blue-100 animate-spin-slow">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4 bg-blue-600 rounded-full"></div>
        </div>
      </div>

      {/* Middle ring */}
      <div className="absolute inset-0 flex items-center justify-center animate-spin-reverse">
        <div className="w-28 h-28 rounded-full border-4 border-purple-100">
          <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-purple-500 rounded-full"></div>
        </div>
      </div>

      {/* Center icon */}
      <div className="relative z-10 bg-linear-to-br from-blue-500 to-purple-600 rounded-full p-6 shadow-lg animate-pulse">
        <Sparkles className="w-12 h-12 text-white" />
      </div>

      <style jsx>{`
        @keyframes spin-slow {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes spin-reverse {
          from { transform: rotate(360deg); }
          to { transform: rotate(0deg); }
        }
        .animate-spin-slow {
          animation: spin-slow 3s linear infinite;
        }
        .animate-spin-reverse {
          animation: spin-reverse 4s linear infinite;
        }
      `}</style>
    </div>
  );
}

// Clean no active jobs illustration with corgi mascot
function NoActiveIllustration() {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {/* Corgi Mascot */}
      <div className="relative z-10 animate-float-gentle">
        <img
          src="/images/corgi-mascot.png"
          alt="Happy Corgi Mascot"
          className="w-48 h-48 object-contain"
        />
      </div>

      {/* Floating sparkles around the corgi */}
      <div className="absolute top-8 right-12 w-2 h-2 bg-blue-400 rounded-full animate-sparkle"></div>
      <div className="absolute bottom-12 left-8 w-3 h-3 bg-purple-400 rounded-full animate-sparkle-delayed"></div>
      <div className="absolute top-16 left-12 w-2 h-2 bg-blue-300 rounded-full animate-sparkle-slow"></div>
      <div className="absolute bottom-16 right-16 w-2 h-2 bg-purple-300 rounded-full animate-sparkle"></div>

      <style jsx>{`
        @keyframes float-gentle {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-15px); }
        }
        @keyframes sparkle {
          0%, 100% { transform: scale(0) translateY(0); opacity: 0; }
          50% { transform: scale(1) translateY(-10px); opacity: 1; }
        }
        @keyframes sparkle-delayed {
          0%, 100% { transform: scale(0) translateY(0); opacity: 0; }
          50% { transform: scale(1) translateY(-8px); opacity: 0.8; }
        }
        @keyframes sparkle-slow {
          0%, 100% { transform: scale(0) translateY(0); opacity: 0; }
          50% { transform: scale(1) translateY(-6px); opacity: 0.6; }
        }
        .animate-float-gentle {
          animation: float-gentle 3s ease-in-out infinite;
        }
        .animate-sparkle {
          animation: sparkle 2s ease-in-out infinite;
        }
        .animate-sparkle-delayed {
          animation: sparkle-delayed 2s ease-in-out infinite 0.5s;
        }
        .animate-sparkle-slow {
          animation: sparkle-slow 2s ease-in-out infinite 1s;
        }
      `}</style>
    </div>
  );
}

// Clean no history illustration
function NoHistoryIllustration() {
  return (
    <div className="relative w-full h-full flex items-center justify-center">
      {/* Background glow */}
      <div className="absolute inset-0 bg-linear-to-br from-gray-100 to-slate-50 rounded-full opacity-50"></div>

      {/* Stacked documents */}
      <div className="relative">
        {/* Back document */}
        <div className="absolute -top-2 -right-2 w-24 h-32 bg-gray-200 rounded-lg shadow-md transform rotate-6 opacity-60"></div>

        {/* Middle document */}
        <div className="absolute -top-1 -right-1 w-24 h-32 bg-gray-300 rounded-lg shadow-md transform rotate-3 opacity-80"></div>

        {/* Front document */}
        <div className="relative w-24 h-32 bg-white rounded-lg shadow-xl border-2 border-gray-200 flex flex-col items-center justify-center p-4">
          <FileText className="w-12 h-12 text-gray-400 mb-2" />
          <div className="w-full space-y-1">
            <div className="h-1 bg-gray-200 rounded"></div>
            <div className="h-1 bg-gray-200 rounded w-3/4"></div>
            <div className="h-1 bg-gray-200 rounded w-1/2"></div>
          </div>
        </div>
      </div>

      {/* Floating clock indicator */}
      <div className="absolute -bottom-2 -right-2 bg-blue-500 rounded-full p-3 shadow-lg animate-bounce-slow">
        <Clock className="w-6 h-6 text-white" />
      </div>

      <style jsx>{`
        @keyframes bounce-slow {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-10px); }
        }
        .animate-bounce-slow {
          animation: bounce-slow 2s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}
