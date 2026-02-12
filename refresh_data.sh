#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists and NOT in Docker
if [ -d ".venv" ] && [ ! -f /.dockerenv ]; then
    source .venv/bin/activate
fi

echo "Starting daily refresh at $(date)" >> refresh.log

# 1. Update the list of active US tickers
echo "Updating symbol list..." >> refresh.log
python3 -m postmorty.main update-symbols >> refresh.log 2>&1

# 2. Ingest data for ALL US symbols (Limit 10000 covers the market)
# Fetch 5 days to cover weekends/holidays and ensure no gaps.
echo "Ingesting daily data..." >> refresh.log
python3 -m postmorty.main ingest-batch --days 5 --symbols-file all_us_symbols.txt --limit 10000 >> refresh.log 2>&1

# 3. Process indicators for ALL US symbols
echo "Processing indicators..." >> refresh.log
python3 -m postmorty.main process-batch --symbols-file all_us_symbols.txt --limit 10000 >> refresh.log 2>&1

# 4. Ingest Valuation Data
echo "Ingesting valuations..." >> refresh.log
python3 -m postmorty.main ingest-valuations --symbols-file all_us_symbols.txt --limit 10000 >> refresh.log 2>&1

echo "Daily refresh complete at $(date)" >> refresh.log
