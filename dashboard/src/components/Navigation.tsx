"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { 
  HomeIcon, 
  ShieldCheckIcon, 
  ChartBarIcon, 
  CpuChipIcon,
  ExclamationTriangleIcon,
  DocumentChartBarIcon,
  BeakerIcon,
  ClockIcon,
  DocumentTextIcon,
  BoltIcon
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Overview', href: '/', icon: HomeIcon },
  { name: 'Compliance', href: '/compliance', icon: ShieldCheckIcon },
  { name: 'Alphas', href: '/alphas', icon: ChartBarIcon },
  { name: 'Risk Monitor', href: '/risk', icon: ExclamationTriangleIcon },
  { name: 'Trades', href: '/trades', icon: DocumentTextIcon },
  { name: 'Performance', href: '/performance', icon: BoltIcon },
  { name: 'Regime Stats', href: '/regime', icon: DocumentChartBarIcon },
  { name: 'Learning', href: '/learning', icon: CpuChipIcon },
  { name: 'Session Report', href: '/report', icon: BeakerIcon },
];

export default function Navigation() {
  const pathname = usePathname();
  const [istTime, setIstTime] = useState<string>('');

  // Format IST time
  const formatISTTime = (date: Date): string => {
    // IST is UTC+5:30
    const istOffset = 5.5 * 60; // minutes
    const istTime = new Date(date.getTime() + istOffset * 60000);
    
    const hours = istTime.getUTCHours().toString().padStart(2, '0');
    const minutes = istTime.getUTCMinutes().toString().padStart(2, '0');
    const seconds = istTime.getUTCSeconds().toString().padStart(2, '0');
    
    return `${hours}:${minutes}:${seconds}`;
  };

  useEffect(() => {
    // Update IST time every second
    const updateTime = () => {
      setIstTime(formatISTTime(new Date()));
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <h1 className="text-xl font-bold text-white">
                Quant Ω Supra AI
              </h1>
              <p className="text-xs text-gray-400">VPropTrader System</p>
            </div>
          </div>

          {/* IST Clock - Desktop */}
          <div className="hidden lg:flex items-center space-x-2 px-4 py-2 bg-gray-800 rounded-lg">
            <ClockIcon className="h-5 w-5 text-blue-400" />
            <div className="text-right">
              <div className="text-xs text-gray-400">Indian Time</div>
              <div className="text-lg font-mono font-bold text-blue-400">
                {istTime} IST
              </div>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="hidden md:block">
            <div className="ml-10 flex items-baseline space-x-4">
              {navigation.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`
                      flex items-center px-3 py-2 rounded-md text-sm font-medium
                      transition-colors duration-200
                      ${isActive
                        ? 'bg-gray-800 text-white'
                        : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                      }
                    `}
                  >
                    <Icon className="h-5 w-5 mr-2" />
                    {item.name}
                  </Link>
                );
              })}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              type="button"
              className="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-white hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white"
            >
              <span className="sr-only">Open main menu</span>
              <svg
                className="block h-6 w-6"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 6h16M4 12h16M4 18h16"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Mobile menu */}
      <div className="md:hidden">
        <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            const Icon = item.icon;
            
            return (
              <Link
                key={item.name}
                href={item.href}
                className={`
                  flex items-center px-3 py-2 rounded-md text-base font-medium
                  ${isActive
                    ? 'bg-gray-800 text-white'
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                  }
                `}
              >
                <Icon className="h-5 w-5 mr-3" />
                {item.name}
              </Link>
            );
          })}
        </div>
      </div>
    </nav>
  );
}
