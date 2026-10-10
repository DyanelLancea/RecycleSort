#!/bin/bash
set -euo pipefail
REGION=us-east-1
DB_URL=$(aws ssm get-parameter --name /recyclesort/prod/database_url --with-decryption --query Parameter.Value --output text --region $REGION)
umask 077
cat > /etc/recyclesort.env <<ENV
APP_ENV=production
AWS_REGION=$REGION
SSM_PREFIX=/recyclesort/prod/
DATABASE_URL=$DB_URL
JWT_EXPIRE_MINUTES=60
ENV
