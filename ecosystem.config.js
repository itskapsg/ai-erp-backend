module.exports = {
  apps: [
    {
      name: 'erp-backend',
      script: '/root/workspace/venv/bin/python3',
      args: '-m uvicorn app.main:app --host 0.0.0.0 --port 8000',
      cwd: '/root/workspace',
      env: {
        PORT: 8000,
        DATABASE_URL: "postgresql://erp_admin:db_password_123@localhost/erp_dev_db",
        PYTHONPATH: "/root/workspace",
        GEMINI_API_KEY: process.env.GEMINI_API_KEY // Ensure this is loaded if pm2 can access .env, mostly better to assume loading from file
      },
      output: '/root/workspace/backend.log',
      error: '/root/workspace/backend_error.log'
    },
    {
      name: 'erp-frontend',
      cwd: '/root/workspace/frontend',
      script: 'npm',
      args: 'run dev -- --host 0.0.0.0 --port 56000',
      env: {
        PORT: 56000
      }
    }
  ]
};