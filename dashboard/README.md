# Vproptrader Dashboard

Next.js web dashboard for real-time monitoring and analytics.

## Setup

```bash
# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with Sidecar API URL

# Run development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Features

- **Overview**: Real-time equity, PnL, drawdown, target progress
- **Compliance**: VPropTrader rule monitoring with status lights
- **Alpha Heatmap**: Performance metrics for each alpha strategy
- **Regime Stats**: Performance by market regime
- **Risk Monitor**: VaR, ES95, volatility, exposure
- **Learning**: Model training progress and drift detection
- **Session Report**: Daily summary with export functionality

## Build

```bash
# Production build
npm run build

# Start production server
npm start
```

## Deployment

Deploy to Vercel, Netlify, or any Node.js hosting platform.

```bash
# Vercel
vercel deploy

# Netlify
netlify deploy --prod
```
