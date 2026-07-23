#!/bin/bash

set -euo pipefail

FILE1="data/public_it_tickets.csv"
FILE2="data/synthetic_tickets.csv"
OUTPUT_FILE="data/combined_ticket.csv"

echo "Combining Files"

head -n 1 "$FILE1" > "$OUTPUT_FILE"
tail -n +2 "$FILE1" >> "$OUTPUT_FILE"
tail -n +2 "$FILE2" >> "$OUTPUT_FILE"

echo "Combined dataset created at: $OUTPUT_FILE"

echo "Starting Model Training"
cd /app
python3 -m ml.train