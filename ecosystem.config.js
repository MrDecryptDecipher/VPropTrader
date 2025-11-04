module.exports = {
  apps: [
    {
      name: 'vproptrader-sidecar',
      script: 'python3',
      args: '-m uvicorn app.main:app --host 127.0.0.1 --port 8001',
      cwd: '/home/ubuntu/Sandeep/projects/Vproptrader/sidecar',
      interpreter: 'none',
      env: {
        PYTHONPATH: '/home/ubuntu/Sandeep/projects/Vproptrader/sidecar',
        HOST: '127.0.0.1',
        PORT: '8001',
        ENVIRONMENT: 'production'
      },
      error_file: '/home/ubuntu/Sandeep/projects/Vproptrader/logs/sidecar-error.log',
      out_file: '/home/ubuntu/Sandeep/projects/Vproptrader/logs/sidecar-out.log',
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
      cwd: '/home/ubuntu/Sandeep/projects/Vproptrader/dashboard',
      interpreter: 'none',
      env: {
        NODE_ENV: 'development',
        PORT: '3001',
        NEXT_PUBLIC_API_URL: 'http://3.111.22.56:8000',
        NEXT_PUBLIC_WS_URL: '3.111.22.56:8000'
      },
      error_file: '/home/ubuntu/Sandeep/projects/Vproptrader/logs/dashboard-error.log',
      out_file: '/home/ubuntu/Sandeep/projects/Vproptrader/logs/dashboard-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      autorestart: true,
      max_restarts: 10,
      min_uptime: '10s',
      restart_delay: 4000
    }
  ]
};
