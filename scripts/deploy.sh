#!/bin/bash

set -e

ENVIRONMENT=${1:-staging}
DEPLOY_PATH="/opt/gravit-system"

echo "Deploying Gravit System to $ENVIRONMENT"

cd $DEPLOY_PATH
git pull origin main

docker-compose -f infra/docker-compose.yml down
docker-compose -f infra/docker-compose.yml pull
docker-compose -f infra/docker-compose.yml up -d

docker system prune -f

echo "Deployment completed"
