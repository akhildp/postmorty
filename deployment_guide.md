# Postmorty Deployment Guide

## 1. System Preparation
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-venv python3-pip postgresql postgresql-contrib
```

## 2. Database Setup
```sql
sudo -i -u postgres psql
CREATE DATABASE postmorty;
CREATE USER alphaseeker WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE postmorty TO alphaseeker;
\q
```

## 3. Installation
```bash
git clone <your-repo>
cd postmorty
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. Initialization
1. Edit `.env` with your VPS-specific details and Alpha Vantage key.
2. Run `python3 -m postmorty.scripts.init_db` to create tables.

## 5. Automation
Add to `crontab -e`:
`0 0 * * * /bin/bash /home/your_user/postmorty/refresh_data.sh`
