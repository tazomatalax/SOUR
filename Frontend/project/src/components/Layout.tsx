import React from 'react';
import { Menu, Settings, Database, LineChart, Brain } from 'lucide-react';
import Sidebar from './Sidebar';

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const navItems = [
    { icon: <LineChart size={24} />, label: 'Dashboard', href: '/' },
    { icon: <Settings size={24} />, label: 'Settings', href: '/settings' },
    { icon: <Database size={24} />, label: 'Export', href: '/export' },
    { icon: <Brain size={24} />, label: 'AI Insights', href: '/insights' },
  ];

  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar navItems={navItems} />
      <main className="flex-1 overflow-auto p-8">
        {children}
      </main>
    </div>
  );
}