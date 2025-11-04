'use client';

import React, { useEffect, useState } from 'react';

interface MarketSession {
  name: string;
  utcStart: string;
  utcEnd: string;
  istStart: string;
  istEnd: string;
  isActive: boolean;
  nextStart: Date | null;
  timeUntil: string;
  status: 'active' | 'upcoming' | 'closed';
}

export default function MarketTimer() {
  const [currentTime, setCurrentTime] = useState<Date>(new Date());
  const [sessions, setSessions] = useState<MarketSession[]>([]);

  // Calculate session times and status
  const calculateSessions = (now: Date): MarketSession[] => {
    const utcHours = now.getUTCHours();
    const utcMinutes = now.getUTCMinutes();
    const utcDay = now.getUTCDay(); // 0 = Sunday, 6 = Saturday
    
    // London session: 07:00-10:00 UTC = 12:30-15:30 IST
    const londonStartUTC = 7;
    const londonEndUTC = 10;
    
    // NY session: 13:30-16:00 UTC = 19:00-21:30 IST
    const nyStartUTC = 13.5;
    const nyEndUTC = 16;
    
    // Check if weekend (no trading)
    const isWeekend = utcDay === 0 || utcDay === 6;
    
    // Current time in decimal hours
    const currentUTCTime = utcHours + utcMinutes / 60;
    
    // London session
    const londonActive = !isWeekend && currentUTCTime >= londonStartUTC && currentUTCTime < londonEndUTC;
    let londonNextStart: Date | null = null;
    let londonTimeUntil = '';
    let londonStatus: 'active' | 'upcoming' | 'closed' = 'closed';
    
    if (londonActive) {
      londonStatus = 'active';
      const endTime = new Date(now);
      endTime.setUTCHours(londonEndUTC, 0, 0, 0);
      const minutesRemaining = Math.floor((endTime.getTime() - now.getTime()) / 60000);
      const hours = Math.floor(minutesRemaining / 60);
      const mins = minutesRemaining % 60;
      londonTimeUntil = `LIVE - ${hours}h ${mins}m remaining`;
    } else {
      // Calculate next London session
      londonNextStart = new Date(now);
      
      if (isWeekend) {
        // Move to next Monday
        const daysUntilMonday = utcDay === 0 ? 1 : 2; // Sunday -> 1 day, Saturday -> 2 days
        londonNextStart.setUTCDate(londonNextStart.getUTCDate() + daysUntilMonday);
        londonNextStart.setUTCHours(londonStartUTC, 0, 0, 0);
      } else if (currentUTCTime >= londonEndUTC) {
        // After London session today, move to tomorrow
        londonNextStart.setUTCDate(londonNextStart.getUTCDate() + 1);
        londonNextStart.setUTCHours(londonStartUTC, 0, 0, 0);
        
        // Check if tomorrow is weekend
        if (londonNextStart.getUTCDay() === 6) {
          // Saturday, move to Monday
          londonNextStart.setUTCDate(londonNextStart.getUTCDate() + 2);
        } else if (londonNextStart.getUTCDay() === 0) {
          // Sunday, move to Monday
          londonNextStart.setUTCDate(londonNextStart.getUTCDate() + 1);
        }
      } else {
        // Before London session today
        londonNextStart.setUTCHours(londonStartUTC, 0, 0, 0);
      }
      
      const minutesUntil = Math.floor((londonNextStart.getTime() - now.getTime()) / 60000);
      const hours = Math.floor(minutesUntil / 60);
      const mins = minutesUntil % 60;
      londonTimeUntil = `${hours}h ${mins}m`;
      londonStatus = 'upcoming';
    }
    
    // NY session
    const nyActive = !isWeekend && currentUTCTime >= nyStartUTC && currentUTCTime < nyEndUTC;
    let nyNextStart: Date | null = null;
    let nyTimeUntil = '';
    let nyStatus: 'active' | 'upcoming' | 'closed' = 'closed';
    
    if (nyActive) {
      nyStatus = 'active';
      const endTime = new Date(now);
      endTime.setUTCHours(Math.floor(nyEndUTC), (nyEndUTC % 1) * 60, 0, 0);
      const minutesRemaining = Math.floor((endTime.getTime() - now.getTime()) / 60000);
      const hours = Math.floor(minutesRemaining / 60);
      const mins = minutesRemaining % 60;
      nyTimeUntil = `LIVE - ${hours}h ${mins}m remaining`;
    } else {
      // Calculate next NY session
      nyNextStart = new Date(now);
      
      if (isWeekend) {
        // Move to next Monday
        const daysUntilMonday = utcDay === 0 ? 1 : 2;
        nyNextStart.setUTCDate(nyNextStart.getUTCDate() + daysUntilMonday);
        nyNextStart.setUTCHours(Math.floor(nyStartUTC), (nyStartUTC % 1) * 60, 0, 0);
      } else if (currentUTCTime >= nyEndUTC) {
        // After NY session today, move to tomorrow
        nyNextStart.setUTCDate(nyNextStart.getUTCDate() + 1);
        nyNextStart.setUTCHours(Math.floor(nyStartUTC), (nyStartUTC % 1) * 60, 0, 0);
        
        // Check if tomorrow is weekend
        if (nyNextStart.getUTCDay() === 6) {
          nyNextStart.setUTCDate(nyNextStart.getUTCDate() + 2);
        } else if (nyNextStart.getUTCDay() === 0) {
          nyNextStart.setUTCDate(nyNextStart.getUTCDate() + 1);
        }
      } else {
        // Before NY session today
        nyNextStart.setUTCHours(Math.floor(nyStartUTC), (nyStartUTC % 1) * 60, 0, 0);
      }
      
      const minutesUntil = Math.floor((nyNextStart.getTime() - now.getTime()) / 60000);
      const hours = Math.floor(minutesUntil / 60);
      const mins = minutesUntil % 60;
      nyTimeUntil = `${hours}h ${mins}m`;
      nyStatus = 'upcoming';
    }
    
    return [
      {
        name: 'London',
        utcStart: '07:00',
        utcEnd: '10:00',
        istStart: '12:30',
        istEnd: '15:30',
        isActive: londonActive,
        nextStart: londonNextStart,
        timeUntil: londonTimeUntil,
        status: londonStatus,
      },
      {
        name: 'New York',
        utcStart: '13:30',
        utcEnd: '16:00',
        istStart: '19:00',
        istEnd: '21:30',
        isActive: nyActive,
        nextStart: nyNextStart,
        timeUntil: nyTimeUntil,
        status: nyStatus,
      },
    ];
  };

  useEffect(() => {
    // Update every second
    const interval = setInterval(() => {
      const now = new Date();
      setCurrentTime(now);
      setSessions(calculateSessions(now));
    }, 1000);

    // Initial calculation
    const now = new Date();
    setCurrentTime(now);
    setSessions(calculateSessions(now));

    return () => clearInterval(interval);
  }, []);

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

  return (
    <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-200">Market Sessions</h3>
        <div className="text-right">
          <div className="text-sm text-gray-400">Current Time (IST)</div>
          <div className="text-xl font-mono font-bold text-blue-400">
            {formatISTTime(currentTime)} IST
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sessions.map((session) => (
          <div
            key={session.name}
            className={`p-4 rounded-lg border-2 ${
              session.isActive
                ? 'border-green-500 bg-green-900/20'
                : 'border-gray-600 bg-gray-700/50'
            }`}
          >
            <div className="flex items-center justify-between mb-2">
              <h4 className="text-md font-semibold text-gray-200">{session.name}</h4>
              {session.isActive && (
                <span className="px-2 py-1 text-xs font-bold text-white bg-green-500 rounded-full animate-pulse">
                  LIVE
                </span>
              )}
            </div>

            <div className="space-y-1 text-sm">
              <div className="flex justify-between text-gray-400">
                <span>IST:</span>
                <span className="font-mono text-gray-300">
                  {session.istStart} - {session.istEnd}
                </span>
              </div>
              <div className="flex justify-between text-gray-500">
                <span>UTC:</span>
                <span className="font-mono">
                  {session.utcStart} - {session.utcEnd}
                </span>
              </div>
            </div>

            <div className="mt-3 pt-3 border-t border-gray-600">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-400">
                  {session.isActive ? 'Time Remaining' : 'Starts In'}
                </span>
                <span
                  className={`text-lg font-mono font-bold ${
                    session.isActive ? 'text-green-400' : 'text-blue-400'
                  }`}
                >
                  {session.timeUntil}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-4 pt-4 border-t border-gray-700">
        <div className="flex items-center justify-center space-x-2 text-xs text-gray-500">
          <span>Trading Hours:</span>
          <span>Monday-Friday</span>
          <span>•</span>
          <span>No Weekend Trading</span>
        </div>
      </div>
    </div>
  );
}
