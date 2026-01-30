module.exports = {
  apps: [
    {
      name: 'erp-backend',
      script: '/workspace/venvs/production/bin/python',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 54279',
      cwd: '/workspace',
      env: {
        PORT: 54279,
        DATABASE_URL: "postgresql://erp_admin:db_password_123@localhost/erp_dev_db",
        PYTHONPATH: "/workspace"
      },
      output: '/tmp/erp-backend-out.log',
      error: '/tmp/erp-backend-error.log'
    },
    {
      name: 'erp-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run dev',
      env: {
        PORT: 56000,
        VITE_API_URL: "http://95.111.253.134:54279"
      }
    }
  ]
};