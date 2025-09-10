#! /bin/bash

docker run \
    --name data-collection \
    --network data-col-net \
    -p 8100:8100 \
    kameldin/speech-data-collection:latest
