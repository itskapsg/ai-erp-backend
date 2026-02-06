
# Deployment Guide

## 1. Prerequisites
Ensure your server has the following installed:
- **Git**: `sudo apt install git`
- **Python 3.10+**: `sudo apt install python3 python3-venv python3-pip`
- **Node.js 18+**:
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```

## 2. Installation
1. Clone the repository:
   ```bash
   git clone <repo_url>
   cd <repo_name>
   ```

2. Run the installer:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

3. Follow the on-screen prompts.
   - The script will set up the Virtual Environment, Install Dependencies, Build the Frontend, and Start the Servers via PM2.

## 3. Post-Install
- **Edit Configuration**:
  Open `.env` and update your settings (Database URL, API Keys).
  ```bash
  nano .env
  ```
  If you change `.env`, restart the backend: `pm2 restart erp-backend`.

- **Create Admin User**:
  ```bash
  source venv/bin/activate
  python3 fix_admin_user.py
  ```

## 4. Maintenance
- **Restart Servers**: `pm2 restart all`
- **View Logs**: `pm2 logs`
- **Update System**:
  ```bash
  git pull
  ./install.sh # Re-runs setup to ensure dependencies are up to date
  ```
