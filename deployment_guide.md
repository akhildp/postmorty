# Docker Deployment Guide - Postmorty

Containerization is the easiest way to deploy Postmorty to your VPS.

## 1. System Preparation (VPS)
### 1.1 Create Deployment User
It is best practice to run Docker as a non-root user.
```bash
# Create user
sudo adduser deployuser

# Add to docker group (and sudo if needed)
sudo usermod -aG docker deployuser
sudo usermod -aG sudo deployuser

# Switch to the new user
su - deployuser
```

### 1.2 Install Docker
Install Docker and Docker Compose (if not already installed):
```bash
sudo apt update
sudo apt install -y docker.io docker-compose-v2
sudo systemctl enable --now docker
# Log out and log back in for group changes to take effect
exit
su - deployuser
```

## 2. Configuration
1. **Clone the Repo** (as `deployuser`):
   ```bash
   git clone https://github.com/akhildp/postmorty.git
   cd postmorty
   ```
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

Calcluate indicators for all S&P 500 symbols:
```bash
docker compose exec app python3 -m postmorty.main process-sp500
```

## 5. Automation (Cron)
Add to `crontab -e` (as `deployuser`):
```cron
0 0 * * * cd /home/deployuser/postmorty && docker compose exec -T app bash refresh_data.sh
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
    - **User**: `deployuser`.
    - **Local Port**: `5433`.
    - **Remote Host**: `127.0.0.1`.
    - **Remote Port**: `5432`.

## 7. Troubleshooting
- **EOF Error (Remote)**: Ensure the SSH Tunnel **Remote Host** is `127.0.0.1` and **Remote Port** is `5432`.
- **Port Conflict**: On the VPS, run `ss -lntp | grep 5432`. If it's empty after `docker compose up`, force a restart: `docker compose down && docker compose up -d`.
- **Permission Denied**: Ensure `deployuser` is in the `docker` group.

## 8. Expanding to All US Stocks
To track ~10,000 active US stocks instead of just the S&P 500:

1.  **Update Symbol List**:
    ```bash
    docker compose exec app python3 -m postmorty.main update-symbols
    ```
    This creates `data/all_us_symbols.txt`.

2.  **Ingest Data** (Limit increased to 10,000):
    ```bash
    docker compose exec app python3 -m postmorty.main ingest-batch --symbols-file all_us_symbols.txt --limit 10000
    ```

3.  **Process Indicators**:
    ```bash
    docker compose exec app python3 -m postmorty.main process-batch --symbols-file all_us_symbols.txt --limit 10000
    ```

4.  **Update Cron**:
    The `refresh_data.sh` script has been updated to automatically:
    -   Fetch the latest ticker list.
    -   Ingest data for all ~10,000 symbols.
    -   Process indicators for all symbols.
    
    Ensure your cron job is running:
    ```cron
    0 0 * * * cd /home/deployuser/postmorty && docker compose exec -T app bash refresh_data.sh
    ```
