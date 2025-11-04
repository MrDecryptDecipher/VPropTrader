import type { Metadata } from "next";
import "./globals.css";
import Navigation from "@/components/Navigation";
import ConnectionStatus from "@/components/ConnectionStatus";

export const metadata: Metadata = {
  title: "Quant Ω Supra AI Dashboard",
  description: "Memory-Adaptive Prop Trading System - VPropTrader",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-gray-950 text-white min-h-screen antialiased">
        <div className="flex flex-col min-h-screen">
          {/* Navigation */}
          <Navigation />
          
          {/* Connection Status Bar */}
          <ConnectionStatus />
          
          {/* Main Content */}
          <main className="flex-1">
            {children}
          </main>
          
          {/* Footer */}
          <footer className="bg-gray-900 border-t border-gray-800 py-4">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <p className="text-center text-sm text-gray-400">
                Quant Ω Supra AI © 2025 | VPropTrader Compliant System
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
