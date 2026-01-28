module.exports = {
  apps: [
    {
      name: 'erp-backend',
      script: '/root/workspace/venv/bin/python',
      args: ['-m', 'uvicorn', 'app.main:app', '--host', '0.0.0.0', '--port', '54279'],
      cwd: '/root/workspace',
      env: { 
        PYTHONPATH: "/root/workspace"
      }
    },
    {
      name: 'erp-frontend',
      cwd: '/root/workspace/frontend',
      script: 'npm',
      args: ['run', 'dev', '--', '--host', '0.0.0.0', '--port', '56000']
    },
    {
      name: 'openhands-agent',
      script: '/root/start-openhands.sh',
      env: {
        WORKSPACE_BASE: '/root/workspace'
      }
    }
  ]
};
