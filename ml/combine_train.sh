#!/bin/bash

set -euo pipefail

echo "Downloading training datasets from S3"
cd /app
python3 -m ml.download_files

FILE1="/tmp/data/public_it_tickets.csv"
FILE2="/tmp/data/synthetic_tickets.csv"
OUTPUT_FILE="/tmp/data/combined_ticket.csv"

echo "Combining files"

head -n 1 "$FILE1" > "$OUTPUT_FILE"
tail -n +2 "$FILE1" >> "$OUTPUT_FILE"
tail -n +2 "$FILE2" >> "$OUTPUT_FILE"

echo "Combined dataset created at: $OUTPUT_FILE"

echo "Starting model training"
python3 -m ml.train

echo "Uploading generated files to S3"
python3 -m ml.upload_files

echo "Training pipeline completed successfully"