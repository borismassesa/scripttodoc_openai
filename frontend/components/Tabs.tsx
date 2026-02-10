'use client';

import { FilePlus, Clock, History, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export type TabId = 'create' | 'active' | 'history';

interface Tab {
  id: TabId;
  label: string;
  icon: React.ReactNode;
  badge?: number;
  description?: string;
}

interface TabsProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  activeJobsCount?: number;
}

export default function Tabs({ activeTab, onTabChange, activeJobsCount = 0 }: TabsProps) {
  const tabs: Tab[] = [
    {
      id: 'create',
      label: 'Create',
      icon: <FilePlus className="h-5 w-5" />,
      description: 'Upload new transcript',
    },
    {
      id: 'active',
      label: 'Active',
      icon: <Clock className="h-5 w-5" />,
      badge: activeJobsCount > 0 ? activeJobsCount : undefined,
      description: 'Processing jobs',
    },
    {
      id: 'history',
      label: 'History',
      icon: <History className="h-5 w-5" />,
      description: 'Completed documents',
    },
  ];

  return (
    <nav className="flex flex-col space-y-1 px-2" aria-label="Tabs">
      {tabs.map((tab) => {
        const isActive = activeTab === tab.id;
        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              'group relative flex items-center space-x-3 px-3 py-2 text-sm font-medium transition-all duration-150 rounded-md',
              isActive
                ? 'text-gray-900 bg-gray-100'
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
            )}
            aria-current={isActive ? 'page' : undefined}
          >
            {/* Icon */}
            <div
              className={cn(
                'flex items-center justify-center transition-colors',
                isActive
                  ? 'text-gray-900'
                  : 'text-gray-500 group-hover:text-gray-700'
              )}
            >
              {tab.icon}
            </div>
            
            {/* Label and Description */}
            <div className="flex-1 text-left min-w-0">
              <div className="flex items-center justify-between">
                <span className={cn(
                  'font-medium',
                  isActive ? 'text-gray-900' : 'text-gray-700'
                )}>
                  {tab.label}
                </span>
                {tab.badge !== undefined && (
                  <span
                    className={cn(
                      'ml-2 inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-xs font-medium rounded-full transition-colors',
                      isActive
                        ? 'bg-gray-900 text-white'
                        : 'bg-gray-200 text-gray-600 group-hover:bg-gray-300'
                    )}
                  >
                    {tab.badge}
                  </span>
                )}
              </div>
              {tab.description && (
                <p className={cn(
                  'text-xs mt-0.5 truncate',
                  isActive ? 'text-gray-600' : 'text-gray-500'
                )}>
                  {tab.description}
                </p>
              )}
            </div>
          </button>
        );
      })}
    </nav>
  );
}

