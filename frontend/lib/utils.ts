import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

export function formatDuration(seconds: number): string {
  // Handle negative values (shouldn't happen, but be defensive)
  const absSeconds = Math.abs(seconds);

  if (absSeconds < 1) return 'just now';
  if (absSeconds < 60) return `${Math.round(absSeconds)} secs`;

  const minutes = Math.floor(absSeconds / 60);
  if (minutes < 60) {
    const remainingSeconds = Math.round(absSeconds % 60);
    return remainingSeconds > 0
      ? `${minutes} min ${remainingSeconds} sec`
      : `${minutes} min`;
  }

  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    const remainingMinutes = minutes % 60;
    return remainingMinutes > 0
      ? `${hours} hr ${remainingMinutes} min`
      : `${hours} hr`;
  }

  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours > 0
    ? `${days} day${days !== 1 ? 's' : ''} ${remainingHours} hr`
    : `${days} day${days !== 1 ? 's' : ''}`;
}

export function formatRelativeTime(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diff = now.getTime() - date.getTime();

  const seconds = Math.floor(Math.abs(diff) / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);
  const days = Math.floor(hours / 24);

  // Handle future dates (timezone issues)
  if (diff < 0) {
    return 'just now';
  }

  // Handle very recent
  if (seconds < 5) return 'just now';
  if (seconds < 60) return `${seconds} secs ago`;

  // Minutes
  if (minutes < 60) return `${minutes} min${minutes !== 1 ? 's' : ''} ago`;

  // Hours
  if (hours < 24) return `${hours} hr${hours !== 1 ? 's' : ''} ago`;

  // Days
  return `${days} day${days !== 1 ? 's' : ''} ago`;
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 0.85) return 'text-green-600';
  if (confidence >= 0.7) return 'text-blue-600';
  if (confidence >= 0.5) return 'text-yellow-600';
  return 'text-red-600';
}

export function getConfidenceLabel(confidence: number): string {
  if (confidence >= 0.85) return 'Very High';
  if (confidence >= 0.7) return 'High';
  if (confidence >= 0.5) return 'Medium';
  return 'Low';
}

export function getStatusColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'bg-green-100 text-green-800';
    case 'processing':
      return 'bg-blue-100 text-blue-800';
    case 'queued':
      return 'bg-yellow-100 text-yellow-800';
    case 'failed':
      return 'bg-red-100 text-red-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

