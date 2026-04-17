# Deployment Instructions — AWS Health Notifications Tracker

## Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | System package manager |
| Node.js | 22+ | https://nodejs.org |
| AWS CDK | 2.x | `npm install -g aws-cdk` |
| AWS CLI | 2.x | https://aws.amazon.com/cli |

Your AWS credentials must have permissions to create: Lambda, DynamoDB, S3, CloudFront, API Gateway, Cognito, Bedrock, EventBridge, SNS, IAM, CloudWatch.

---

## One-Command Deployment

```bash
bash scripts/deploy.sh
```

This script:
1. Builds the React frontend (`npm ci && npm run build`)
2. Installs CDK Python dependencies
3. Bootstraps CDK in us-east-1 (idempotent)
4. Deploys all AWS infrastructure via `cdk deploy`
5. Parses CDK outputs and regenerates `frontend/src/aws-exports.ts`
6. Rebuilds frontend with real Cognito + API config
7. Syncs frontend bundle to S3
8. Invalidates CloudFront cache
9. Seeds DynamoDB with 50 realistic mock events

---

## Step-by-Step Manual Deployment

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Install frontend dependencies

```bash
cd frontend && npm ci && cd ..
```

### 3. Bootstrap CDK (first time only)

```bash
cdk bootstrap aws://ACCOUNT_ID/us-east-1
```

### 4. Deploy infrastructure

```bash
cdk deploy --require-approval never --outputs-file cdk-outputs.json
```

CDK will output:
- `CloudFrontURL` — the application URL
- `UserPoolId` — Cognito User Pool ID
- `UserPoolClientId` — Cognito App Client ID
- `ApiEndpoint` — API Gateway URL
- `TableName` — DynamoDB table name
- `FrontendBucketName` — S3 bucket for the SPA
- `DistributionId` — CloudFront distribution ID

### 5. Generate frontend config

```bash
cat > frontend/src/aws-exports.ts << EOF
const awsConfig = {
  userPoolId: '<UserPoolId>',
  userPoolClientId: '<UserPoolClientId>',
  apiEndpoint: '<ApiEndpoint>',
  region: 'us-east-1',
}
export default awsConfig
EOF
```

### 6. Build and deploy frontend

```bash
cd frontend && npm run build && cd ..
aws s3 sync frontend/dist/ s3://<FrontendBucketName>/ --delete
aws cloudfront create-invalidation --distribution-id <DistributionId> --paths "/*"
```

### 7. Seed mock data

```bash
TABLE_NAME=<TableName> python3 scripts/seed_mock_data.py
```

---

## Post-Deployment: Create the First User

Cognito is configured with no self-signup. Create users via CLI:

```bash
# Create user
aws cognito-idp admin-create-user \
  --user-pool-id <UserPoolId> \
  --username admin@example.com \
  --user-attributes Name=email,Value=admin@example.com \
  --temporary-password TempPass123! \
  --region us-east-1

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id <UserPoolId> \
  --username admin@example.com \
  --password PermanentPass123! \
  --permanent \
  --region us-east-1
```

---

## Verify Deployment

```bash
# Check the app loads
curl -s -o /dev/null -w "%{http_code}" <CloudFrontURL>
# Expected: 200

# Check DynamoDB has data
aws dynamodb scan \
  --table-name HealthEvents \
  --select COUNT \
  --region us-east-1
# Expected: Count >= 50
```

---

## Running Tests

```bash
# Python unit tests
pytest lambdas/ -v

# TypeScript type check
cd frontend && tsc --noEmit
```

---

## Tear Down

```bash
cdk destroy --force
```

> Note: S3 buckets are set to `auto_delete_objects=True` so they will be emptied and deleted automatically.

---

## Configuration

Edit `cdk.json` context before deploying:

```json
{
  "context": {
    "admin_email": "your-team@example.com",
    "org_admin_role_arn": "arn:aws:iam::MGMT_ACCOUNT:role/OrganizationAccountAccessRole"
  }
}
```

---

## Architecture Summary

```
EventBridge (15 min)  →  health-collector Lambda  →  DynamoDB (HealthEvents)
                                                              │
                                                              ▼ (DynamoDB Streams)
                                                     llm-summarizer Lambda
                                                              │
                                                              ▼
                                                    Amazon Bedrock (Claude Haiku)

EventBridge (09:00 UTC daily)  →  deadline-reminder Lambda  →  SNS email

Users  →  CloudFront  →  React SPA (S3)
                │
                ▼
          API Gateway HTTP API  →  api-handler Lambda  →  DynamoDB
                │
          Cognito JWT Authorizer
```

**Region**: us-east-1  
**Estimated cost**: ~$10–15/month at steady state
