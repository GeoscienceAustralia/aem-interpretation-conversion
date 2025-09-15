#!/bin/bash
set -exuo pipefail

echo "Setting up environment..."
apt-get update && apt-get install -y python3-pip gdal-bin libgdal-dev

echo "Installing GDAL and Python requirements..."
pip install GDAL==$(gdal-config --version)
pip install -r requirements.txt

