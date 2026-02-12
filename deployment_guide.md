# Docker Deployment Guide - Postmorty

Containerization is the easiest way to deploy Postmorty to your VPS.

## 1. System Preparation (VPS)
Install Docker and Docker Compose:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
# Log out and log back in for group changes to take effect
```

## 2. Configuration
1. **Clone the Repo**.
2. **Edit `.env`**:
   ```ini
   DB_USER=alphaseeker
   DB_PASSWORD=makemerich
   DB_NAME=postmorty
   DB_HOST=db
   DB_PORT=5432
   MASSIVE_API_KEY=your_key_here
   ```

## 3. Deployment
```bash
docker compose up -d --build
```

## 4. Initialize Database & Fetch Data
Initialize the schema:
```bash
docker compose exec app python3 -m postmorty.scripts.init_db
```

Fetch 10 years of data for S&P 500 (this will take time):
```bash
docker compose exec app python3 -m postmorty.main ingest-sp500 --days 3650
```

## 5. Automation (Cron)
Add to `crontab -e`:
```cron
0 0 * * * cd /home/mortyuser/postmorty && sudo docker compose exec -T app bash refresh_data.sh
```

## 6. Remote Access (DBeaver / TablePlus)
The most secure way to access your database is via an **SSH Tunnel**.

### DBeaver Setup Checklist:
1.  **Main Connection Tab**:
    - **Host**: `127.0.0.1`
    - **Port**: `5433` (Use 5433 to avoid local conflicts)
    - **Database**: `postmorty`
    - **Username/Password**: `alphaseeker` / `makemerich`
2.  **SSH Tab**:
    - Check **"Use SSH Tunnel"**.
    - **Host**: Your VPS IP.
    - **User**: `mortyuser`.
    - **Local Port**: `5433`.
    - **Remote Host**: `127.0.0.1`.
    - **Remote Port**: `5432`.

## 7. Troubleshooting
- **EOF Error (Remote)**: Ensure the SSH Tunnel **Remote Host** is `127.0.0.1` and **Remote Port** is `5432`.
- **Port Conflict**: On the VPS, run `ss -lntp | grep 5432`. If it's empty after `docker compose up`, force a restart: `sudo docker compose down && sudo docker compose up -d`.
- **Permission Denied**: Ensure your user is in the `docker` group.
