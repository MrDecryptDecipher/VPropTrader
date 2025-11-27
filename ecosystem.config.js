module.exports = {
  apps: [
    {
      name: 'vproptrader-sidecar',
      script: 'python3',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8001',
      cwd: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/sidecar',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/sidecar',
        HOST: '0.0.0.0',
        PORT: '8001',
        ENVIRONMENT: 'production'
      },
      error_file: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/logs/sidecar-error.log',
      out_file: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/logs/sidecar-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 4000
    },
    {
      name: 'vproptrader-dashboard',
      script: 'npm',
      args: 'run dev',
      cwd: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/dashboard',
      interpreter: 'none',
      env: {
        NODE_ENV: 'development',
        PORT: '3001',
        NEXT_PUBLIC_API_URL: 'http://3.111.22.56:8002',
        NEXT_PUBLIC_WS_URL: '3.111.22.56:8002'
      },
      error_file: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/logs/dashboard-error.log',
      out_file: '/home/ubuntu/Sandeep/projects/Vproptrader/VPropTrader/logs/dashboard-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 4000
    }
  ]
};
