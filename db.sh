#! /bin/bash

docker run \
    --name mysql1 \
    --network data-col-net \
    -e MYSQL_ROOT_PASSWORD=admin \
    -e MYSQL_ROOT_HOST="0.0.0.0" \
    -e MYSQL_USER=root \
    -e MYSQL_PASSWORD=admin \
    -e MYSQL_DATABASE=tts_dataset_generator \
    --mount type=bind,src=/workspaces/Voice-Dataset-Collection/db_mount,dst=/var/lib/mysql \
    -p 3306:3306 \
    -d container-registry.oracle.com/mysql/community-server:latest
