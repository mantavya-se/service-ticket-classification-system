#!/bin/bash
set -euo pipefail

echo "Pulling new data from db and combining with synthetic dataset"
python3 -m retrain.retrain

echo "Validating synthetic dataset"
python3 -m retrain.validate