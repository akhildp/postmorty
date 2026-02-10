#!/bin/bash

# Navigate to the project directory
cd "$(dirname "$0")"

# Activate the virtual environment
source .venv/bin/activate

# Fetch the top 25 companies
echo "Starting daily refresh at $(date)" >> refresh.log
python3 -m postmorty.main ingest-sp500 --limit 25 --symbols-file top_25_market_cap.txt >> refresh.log 2>&1

# Process each ticker in the top 25
while read -r symbol; do
    echo "Processing $symbol..." >> refresh.log
    python3 -m postmorty.main process-ticker "$symbol" >> refresh.log 2>&1
done < data/top_25_market_cap.txt

echo "Daily refresh complete at $(date)" >> refresh.log
