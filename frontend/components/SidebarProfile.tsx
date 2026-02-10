'use client';

import { useState } from 'react';
import { User, Settings, LogOut, ChevronUp, ChevronDown, HelpCircle, Bell } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SidebarProfileProps {
  userName?: string;
  userEmail?: string;
  onLogout?: () => void;
}

export default function SidebarProfile({
  userName = 'User',
  userEmail = 'user@example.com',
  onLogout
}: SidebarProfileProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const menuItems = [
    {
      id: 'settings',
      label: 'Settings',
      icon: <Settings className="h-4 w-4" />,
      onClick: () => console.log('Settings clicked'),
    },
    {
      id: 'notifications',
      label: 'Notifications',
      icon: <Bell className="h-4 w-4" />,
      onClick: () => console.log('Notifications clicked'),
    },
    {
      id: 'help',
      label: 'Help & Support',
      icon: <HelpCircle className="h-4 w-4" />,
      onClick: () => console.log('Help clicked'),
    },
    {
      id: 'logout',
      label: 'Sign Out',
      icon: <LogOut className="h-4 w-4" />,
      onClick: () => {
        if (onLogout) {
          onLogout();
        } else {
          console.log('Logout clicked');
        }
      },
      className: 'text-red-600 hover:text-red-700 hover:bg-red-50',
    },
  ];

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Profile Toggle Button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className={cn(
          'w-full flex items-center space-x-3 px-4 py-3.5 transition-colors',
          'hover:bg-gray-50',
          isExpanded && 'bg-gray-50'
        )}
      >
        <div className="flex-shrink-0">
          <div className="h-10 w-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-md">
            <User className="h-5 w-5 text-white" />
          </div>
        </div>
        <div className="flex-1 text-left min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">{userName}</p>
          <p className="text-xs text-gray-500 truncate">{userEmail}</p>
        </div>
        <div className="flex-shrink-0 text-gray-400">
          {isExpanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronUp className="h-4 w-4" />
          )}
        </div>
      </button>

      {/* Expanded Menu */}
      {isExpanded && (
        <div className="border-t border-gray-100 bg-gray-50/50">
          <div className="py-2">
            {menuItems.map((item) => (
              <button
                key={item.id}
                onClick={item.onClick}
                className={cn(
                  'w-full flex items-center space-x-3 px-4 py-2.5 text-sm transition-colors',
                  'hover:bg-gray-100',
                  item.className || 'text-gray-700 hover:text-gray-900'
                )}
              >
                <div className={cn(
                  'flex-shrink-0',
                  item.id === 'logout' ? 'text-red-500' : 'text-gray-500'
                )}>
                  {item.icon}
                </div>
                <span className="text-left">{item.label}</span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

