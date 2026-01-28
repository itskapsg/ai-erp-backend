module.exports = {
  apps: [
    {
      name: 'erp-backend',
      script: '/root/workspace/venv/bin/python',
      args: ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '54279'],
      cwd: '/root/workspace',
      env: {
        PYTHONPATH: '/root/workspace'
      },
      instances: 1,
      exec_mode: 'fork',
      autorestart: true
    },
    {
      name: 'erp-frontend',
      cwd: '/root/workspace/frontend',
      script: 'npm',
      args: 'run dev -- --host 0.0.0.0 --port 56000',
      instances: 1,
      exec_mode: 'fork',
      autorestart: true
    }
  ]
};
