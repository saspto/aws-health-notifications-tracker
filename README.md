# AWS Health Notifications Tracker

Centralized visibility for AWS Health events across 200+ accounts in an AWS Organization.

## Architecture

```
EventBridge (15min) ──► health-collector Lambda ──► DynamoDB (HealthEvents)
                                │                          │
                                ▼                          ▼ (Streams)
                          S3 Archive              llm-summarizer Lambda
                                                          │
                                                          ▼
EventBridge (daily) ──► deadline-reminder Lambda    Amazon Bedrock
         │                       │                  (Claude Haiku)
         │                       ▼
         │               SNS Topic (email)
         │
Users ──► CloudFront ──► React SPA (S3)
               │
               ▼
         API Gateway ──► api-handler Lambda ──► DynamoDB
               │
         Cognito JWT
```

## Prerequisites

- AWS CLI configured with admin permissions
- Python 3.12+
- Node.js 22+
- AWS CDK v2: `npm install -g aws-cdk`
- AWS account with AWS Organizations and Health API enabled

## Deployment

```bash
# One-command deploy
bash scripts/deploy.sh
```

## Adding Cognito Users

```bash
aws cognito-idp admin-create-user \
  --user-pool-id <UserPoolId from CDK output> \
  --username user@example.com \
  --user-attributes Name=email,Value=user@example.com \
  --temporary-password TempPass123! \
  --region us-east-1
```

## Environment Variables

All environment variables are set automatically by CDK via Lambda environment configuration. No manual configuration required after deployment.

| Variable | Description |
|---|---|
| TABLE_NAME | DynamoDB table name |
| ARCHIVE_BUCKET | S3 bucket for raw event archives |
| SNS_TOPIC_ARN | SNS topic for deadline alerts |
| REGION | AWS region (us-east-1) |

## Running Tests

```bash
# Unit tests
pytest lambdas/ -v

# Frontend type check
cd frontend && tsc --noEmit
```
