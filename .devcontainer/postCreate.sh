#! /bin/bash
cd /workspaces/Voice-Dataset-Collection
uv init --package
uv add --requirements ./requirements.txt
npm i --save-dev @types/node
source /workspaces/Voice-Dataset-Collection/.venv/bin/activate