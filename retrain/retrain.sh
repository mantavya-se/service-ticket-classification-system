#!/bin/bash
set -euo pipefail

cd /app

echo "Downloading synthetic data and pulling new records from RDS"
python3 -m retrain.retrain

echo "Validating synthetic dataset"
python3 -m retrain.validate

echo "Uploading updated synthetic dataset to S3"
python3 -m retrain.upload_outputs

echo "Retraining data update completed"