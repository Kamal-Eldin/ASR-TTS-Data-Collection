#! /bin/bash
cd /workspaces/Voice-Dataset-Collection
uv init --package
uv add --requirements ./requirements.txt
source /workspaces/Voice-Dataset-Collection/.venv/bin/activate