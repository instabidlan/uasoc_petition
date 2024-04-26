#!/bin/bash

docker build -t petitio_bot .
docker run -dp 51337:51337 petitio_bot