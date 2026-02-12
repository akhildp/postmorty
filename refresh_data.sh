#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment if it exists and NOT in Docker
if [ -d ".venv" ] && [ ! -f /.dockerenv ]; then
    source .venv/bin/activate
fi

# Fetch ALL S&P 500 companies
# We fetch 5 days of history to cover weekends/holidays and ensure no gaps.
# The default limit is 600, which covers all 503+ symbols.
echo "Starting daily refresh at $(date)"
echo "Starting daily refresh at $(date)" >> refresh.log
python3 -m postmorty.main ingest-sp500 --days 5 --symbols-file sp500_symbols.txt >> refresh.log 2>&1

# Process each ticker in the S&P 500
# We iterate through the full list now
# Process indicators for all S&P 500 symbols
echo "Starting batch processing..." >> refresh.log
python3 -m postmorty.main process-sp500 >> refresh.log 2>&1

echo "Daily refresh complete at $(date)" >> refresh.log
