module.exports = {
  apps: [{
    name: 'prsnl-frontend',
    script: 'npm',
    args: 'run dev',
    cwd: '/Users/pronav/Personal Knowledge Base/PRSNL/frontend',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      NODE_ENV: 'development',
      PORT: 3002
    },
    error_file: './logs/frontend-error.log',
    out_file: './logs/frontend-out.log',
    log_file: './logs/frontend-combined.log',
    time: true
  }]
};