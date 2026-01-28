module.exports = {
  apps: [
    {
      name: 'openhands-agent',
      script: 'openhands',
      args: 'start --host 0.0.0.0 --port 3000',
      interpreter: 'none',
      env: {
        PATH: '/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
        WORKSPACE_BASE: '/root/workspace'
      }
    }
  ]
};
