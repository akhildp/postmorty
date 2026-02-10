# Docker Deployment Guide - Postmorty

Containerization is the easiest way to deploy Postmorty to your VPS.

## 1. System Preparation (VPS)
Install Docker and Docker Compose:
```bash
sudo apt update
sudo apt install -y docker.io docker-compose
sudo systemctl enable --now docker
```

## 2. Configuration
1. **Clone the Repo** to your VPS.
2. **Edit `.env`**:
   ```ini
   DB_USER=alphaseeker
   DB_PASSWORD=makemerich
   DB_NAME=postmorty
   # When using Docker Compose, the DB host is simply 'db'
   DB_HOST=db
   DB_PORT=5432
   ALPHA_VANTAGE_KEYS=key1,key2
   ```

## 3. Deployment
Run the stack in the background:
```bash
docker-compose up -d --build
```

## 4. Initialize Database
Create the required tables inside the container:
```bash
docker-compose exec app python3 -m postmorty.scripts.init_db
```

## 5. Automation
You can still use `cron` to trigger the refresh inside the container.
Add to `crontab -e`:
```cron
0 0 * * * cd /home/your_user/postmorty && docker-compose exec -T app bash refresh_data.sh
```

## 6. Verification
```bash
docker-compose exec app python3 -m postmorty.main status
```
Check logs:
```bash
docker-compose logs -f app
```
