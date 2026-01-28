module.exports = {
  apps: [
    {
      name: 'erp-backend',
      cwd: '/root/workspace',
      script: '/root/workspace/venv/bin/uvicorn',
      args: 'app.main:app --host 0.0.0.0 --port 54279',
      interpreter: 'none',
      env: { 
        DATABASE_URL: "sqlite:///./test_erp.db",
        ALLOW_ORIGINS: "http://95.111.253.134:56000"
      }
    },
    {
      name: 'erp-frontend',
      cwd: '/root/workspace/frontend',
      script: 'npm',
      args: ['run', 'dev', '--', '--host', '0.0.0.0', '--port', '56000'],
      env: {
        VITE_API_URL: "http://95.111.253.134:54279"
      }
    },
    {
      name: 'openhands-agent',
      script: '/root/.local/bin/openhands',
      args: 'web --headless',
      interpreter: 'none',
      env: {
        WORKSPACE_BASE: '/root/workspace'
      }
    }
  ]
};
