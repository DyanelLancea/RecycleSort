#!/bin/bash
# Creates the rs-target-5xx alarm. The console cannot select HTTPCode_Target_5XX_Count
# until the first 5xx has happened, so this alarm was created with the AWS CLI (CloudShell).
set -euo pipefail
TOPIC_ARN=$(aws sns list-topics --query "Topics[?ends_with(TopicArn, ':rs-alerts')].TopicArn" --output text)
aws cloudwatch put-metric-alarm \
  --alarm-name rs-target-5xx \
  --namespace AWS/ApplicationELB \
  --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value="$ALB_ID" \
  --statistic Sum --period 300 --evaluation-periods 1 \
  --threshold 5 --comparison-operator GreaterThanThreshold \
  --treat-missing-data notBreaching \
  --alarm-actions "$TOPIC_ARN"