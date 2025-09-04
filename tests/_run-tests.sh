#!/bin/bash
set -exuo pipefail

echo "Building conda test environment…"

# move into your project
# cd "${$HOME}"

# install miniconda under $HOME
wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda
export PATH="$HOME/miniconda/bin:$PATH"
eval "$(conda shell.bash hook)"

echo "Bootstrapping mamba…"
# install mamba into base so you can call it directly
conda install -n base -c conda-forge mamba -y

echo "Creating & activating aemworkflow-scripts with mamba…"
mamba env create -f environment.yml -y
conda activate aemworkflow-scripts