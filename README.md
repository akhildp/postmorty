# Postmorty - Stock Trading Analysis CLI

A Python-based CLI tool for ingesting stock data from Alpha Vantage and calculating technical indicators.

## Project Structure
```
postmorty/
├── postmorty/          # Source code package
│   ├── main.py         # CLI entry point
│   ├── api/            # API clients (Alpha Vantage)
│   ├── core/           # Database & Indicator logic
│   └── scripts/        # Initialization scripts
├── data/               # Symbols and configuration data
├── .env                # Environment variables (API keys, DB)
├── requirements.txt    # Project dependencies
└── refresh_data.sh     # Automation script for daily refresh
```

## Deployment Guide (VPS)
For a detailed step-by-step setup on a fresh VPS, see the [Deployment Guide](deployment_guide.md).

## Quick Setup (Docker - Recommended)
1. Clone the repository.
2. Edit `.env` with your API keys.
3. Run: `docker-compose up -d`
4. Initialize the DB: `docker-compose exec app python3 -m postmorty.scripts.init_db`

## Usage (Docker)
```bash
docker-compose exec app python3 -m postmorty.main status
docker-compose exec app python3 -m postmorty.main ingest-daily AAPL
```

## Quick Setup (Manual)
1. Clone the repository.
2. `python3 -m venv .venv && source .venv/bin/activate`
3. `pip install -r requirements.txt`
4. Configure `.env` and `python3 -m postmorty.scripts.init_db`
5. `chmod +x refresh_data.sh`
6. `crontab -e` -> `0 0 * * * /bin/bash /absolute/path/to/refresh_data.sh`

## Usage
Run the CLI as a module:
```bash
python3 -m postmorty.main status
python3 -m postmorty.main ingest-daily AAPL
python3 -m postmorty.main ingest-sp500 --limit 25
python3 -m postmorty.main process-ticker AAPL
```

## Automation
To set up daily refresh via cron:
1. `crontab -e`
2. Add: `0 0 * * * /bin/bash /path/to/postmorty/refresh_data.sh`
