#! /bin/bash
cd /workspaces/Voice-Dataset-Collection
docker pull container-registry.oracle.com/mysql/community-server:9.4.0-aarch64
uv init --package
uv add --requirements ./requirements.txt
source /workspaces/Voice-Dataset-Collection/.venv/bin/activate