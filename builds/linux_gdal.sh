#!/bin/bash
set -exuo pipefail

echo "Setting up environment..."
apt-get update && apt-get install -y python3-pip gdal-bin libgdal-dev

echo "Installing Python GDAL..."
pip install GDAL==$(gdal-config --version)
