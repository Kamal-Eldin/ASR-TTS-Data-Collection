#! /bin/bash
cd /workspaces/Voice-Dataset-Collection
source /workspaces/Voice-Dataset-Collection/secrets/tf_secrets.sh
uv init --package
uv add --requirements ./requirements.txt
npm i --save-dev @types/node
sudo apt update
sudo apt install amazon-ecr-credential-helper
source /workspaces/Voice-Dataset-Collection/.venv/bin/activate