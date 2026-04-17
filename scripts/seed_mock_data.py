#!/usr/bin/env python3
"""Seed DynamoDB with 50 realistic mock AWS Health events."""
import json
import os
import sys
import random
import boto3
from datetime import datetime, timezone, timedelta

TABLE_NAME = os.environ.get("TABLE_NAME", "HealthEvents")
REGION = os.environ.get("REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)

SERVICES = ["ECS", "RDS", "Lambda", "EC2", "S3", "IAM", "CloudFront", "DynamoDB", "OpenSearch", "ELB"]

EVENT_TYPES = {
    "ECS": ["AWS_ECS_MAINTENANCE_SCHEDULED", "AWS_ECS_OPERATIONAL_ISSUE"],
    "RDS": ["AWS_RDS_MAINTENANCE_SCHEDULED", "AWS_RDS_SECURITY_BULLETIN"],
    "Lambda": ["AWS_LAMBDA_RUNTIME_DEPRECATION_NOTICE", "AWS_LAMBDA_OPERATIONAL_ISSUE"],
    "EC2": ["AWS_EC2_MAINTENANCE_SCHEDULED", "AWS_EC2_SYSTEM_REBOOT_MAINTENANCE"],
    "S3": ["AWS_S3_OPERATIONAL_ISSUE", "AWS_S3_API_ISSUE"],
    "IAM": ["AWS_IAM_OPERATIONAL_NOTIFICATION", "AWS_IAM_SECURITY_BULLETIN"],
    "CloudFront": ["AWS_CLOUDFRONT_OPERATIONAL_ISSUE", "AWS_CLOUDFRONT_MAINTENANCE"],
    "DynamoDB": ["AWS_DYNAMODB_MAINTENANCE_SCHEDULED", "AWS_DYNAMODB_OPERATIONAL_ISSUE"],
    "OpenSearch": ["AWS_OPENSEARCH_MAINTENANCE_SCHEDULED", "AWS_OPENSEARCH_DEPRECATION"],
    "ELB": ["AWS_ELB_OPERATIONAL_ISSUE", "AWS_ELB_MAINTENANCE_SCHEDULED"],
}

ACCOUNT_IDS = [
    "111111111111", "222222222222", "333333333333", "444444444444", "555555555555",
    "666666666666", "777777777777", "888888888888", "999999999999", "101010101010",
    "112112112112", "123123123123", "134134134134", "145145145145", "156156156156",
    "167167167167", "178178178178", "189189189189", "190190190190", "201201201201",
]

ACCOUNT_ALIASES = [
    "prod-primary", "prod-secondary", "staging", "dev-team-a", "dev-team-b",
    "security-account", "logging-central", "networking-prod", "analytics-prod", "ml-training",
    "finance-prod", "hr-systems", "marketing-prod", "sales-crm", "data-warehouse",
    "compliance-audit", "backup-archive", "dr-failover", "shared-services", "sandbox",
]

SUMMARIES = {
    "ECS": "AWS is scheduling maintenance on your ECS clusters to apply security patches and performance improvements. This will require a brief restart of your container instances. Your containerized workloads may experience a short period of unavailability.",
    "RDS": "AWS will perform scheduled maintenance on your RDS database instances to apply critical patches. During this window, your databases may be briefly unavailable as the changes are applied. Ensure you have appropriate failover mechanisms in place.",
    "Lambda": "AWS is deprecating Python 3.8 runtime for Lambda functions. Functions using this runtime will stop processing events after the end-of-life date. You need to upgrade your Lambda functions to a supported Python runtime (3.11 or higher).",
    "EC2": "AWS is scheduling hardware maintenance for EC2 instances in your account. The instances listed will be rebooted during the maintenance window. This is required to apply critical firmware and hypervisor updates.",
    "S3": "AWS S3 is experiencing elevated error rates in the us-east-1 region affecting list and get operations. Engineering teams are investigating and working to resolve the issue. Some requests may fail or experience increased latency.",
    "IAM": "AWS is notifying you of a planned update to IAM service endpoints. This change may affect how your applications authenticate with AWS services. Review the new endpoint configuration and update your applications accordingly.",
    "CloudFront": "AWS CloudFront will be updating edge node configurations to improve performance and security. Your distributions may experience brief periods of elevated latency during the maintenance window. No action is required unless you have custom configurations.",
    "DynamoDB": "AWS is performing maintenance on DynamoDB table storage nodes in your region. Your tables may experience brief periods of elevated latency. All data is protected and will remain durable throughout this maintenance.",
    "OpenSearch": "AWS OpenSearch Service is deprecating version 1.x. Your clusters running this version will need to be upgraded to version 2.x before the end-of-life date. Review the migration guide for upgrade instructions.",
    "ELB": "AWS is scheduling maintenance on your Application Load Balancers to apply security and performance updates. Your load balancers will remain operational during maintenance, but there may be a brief connection reset.",
}

ACTIONS = {
    "ECS": ["Schedule a maintenance window and notify your on-call team", "Verify your ECS services have proper health checks configured", "Test your rolling deployment strategy before the maintenance window", "Ensure CloudWatch alarms are set up for cluster health metrics"],
    "RDS": ["Create a manual snapshot before the maintenance window", "Verify your Multi-AZ configuration is active for automatic failover", "Test your application's database reconnection logic", "Review and confirm the maintenance window timing with your team"],
    "Lambda": ["List all Lambda functions using Python 3.8: aws lambda list-functions", "Update each function's runtime to python3.12 using the AWS Console or CLI", "Test updated functions in staging before deploying to production", "Update your CI/CD pipelines to use the new runtime version"],
    "EC2": ["Identify all instances in the affected Availability Zone", "Create AMI backups of critical instances before maintenance", "Schedule the reboot during off-peak hours to minimize impact", "Verify your Auto Scaling groups are configured for multi-AZ redundancy"],
    "S3": ["Implement retry logic with exponential backoff in your S3 clients", "Monitor your application error rates in CloudWatch", "Consider temporarily routing traffic to a different region if critical", "Check the AWS Service Health Dashboard for resolution updates"],
    "IAM": ["Review the IAM endpoint changes in the AWS documentation", "Update your SDK configurations and credential provider chains", "Test authentication flows in a non-production environment first", "Coordinate the change with your security and platform teams"],
    "CloudFront": ["Review your CloudFront distribution settings and custom configurations", "Enable CloudFront access logging to monitor the maintenance impact", "Test your origin failover configuration if applicable", "Update any custom headers or behaviors that may be affected"],
    "DynamoDB": ["Enable DynamoDB Streams if not already configured for change tracking", "Verify your read/write capacity settings are appropriate", "Implement retry logic in your DynamoDB clients", "Monitor DynamoDB metrics in CloudWatch during the maintenance window"],
    "OpenSearch": ["Review the OpenSearch 2.x migration guide in AWS documentation", "Create a snapshot of your indices before upgrading", "Test the upgrade process in a development cluster first", "Update your OpenSearch client libraries to versions compatible with 2.x"],
    "ELB": ["Review your load balancer target group health check configurations", "Verify your application handles connection resets gracefully", "Monitor your ALB access logs during and after maintenance", "Ensure your Auto Scaling policies account for brief traffic fluctuations"],
}

def generate_events() -> list[dict]:
    now = datetime.now(timezone.utc)
    events = []

    deadline_configs = [
        (2, "Critical"),
        (2, "Critical"),
        (3, "Critical"),
        (5, "High"),
        (7, "High"),
        (10, "High"),
        (14, "High"),
        (20, "Medium"),
        (25, "Medium"),
        (30, "Medium"),
        (45, "Low"),
        (60, "Low"),
        (90, "Low"),
    ]

    for i in range(50):
        service = SERVICES[i % len(SERVICES)]
        event_type = EVENT_TYPES[service][i % len(EVENT_TYPES[service])]
        account_idx = i % len(ACCOUNT_IDS)
        account_id = ACCOUNT_IDS[account_idx]
        account_alias = ACCOUNT_ALIASES[account_idx]

        if i < len(deadline_configs):
            days, urgency = deadline_configs[i]
        else:
            days = random.randint(5, 90)
            if days <= 3:
                urgency = "Critical"
            elif days <= 14:
                urgency = "High"
            elif days <= 30:
                urgency = "Medium"
            else:
                urgency = "Low"

        start_time = now - timedelta(days=random.randint(1, 30))
        deadline = now + timedelta(days=days)
        end_time = deadline + timedelta(days=7)
        ttl = int((end_time + timedelta(days=365)).timestamp())

        follow_up_statuses = ["Pending", "Pending", "In Progress", "Resolved"]
        follow_up_status = follow_up_statuses[i % len(follow_up_statuses)]

        event = {
            "eventArn": f"arn:aws:health:us-east-1::event/{service}/{event_type}/{i:04d}",
            "accountId": account_id,
            "accountAlias": account_alias,
            "service": service,
            "eventTypeCode": event_type,
            "eventTypeCategory": "scheduledChange" if "MAINTENANCE" in event_type or "DEPRECAT" in event_type else "issue",
            "region": "us-east-1",
            "startTime": start_time.isoformat(),
            "endTime": end_time.isoformat(),
            "deadline": deadline.isoformat(),
            "lastUpdated": now.isoformat(),
            "statusCode": "open",
            "status": "Open",
            "affectedResources": [
                f"arn:aws:{service.lower()}:us-east-1:{account_id}:resource/{service.lower()}-{i:04d}"
            ],
            "rawEventUrl": f"s3://archive/raw/2026/04/17/{service}_{event_type}_{i:04d}_{account_id}.json",
            "awsHealthUrl": "https://health.aws.amazon.com/health/home#/account/dashboard/open-issues",
            "summary": SUMMARIES.get(service, "AWS Health event requiring your attention."),
            "recommendedActions": ACTIONS.get(service, ["Review the event details", "Take appropriate action"]),
            "urgency": urgency,
            "followUpStatus": follow_up_status,
            "followUpNotes": "Assigned to platform team for review." if follow_up_status == "In Progress" else "",
            "followUpOwner": "ops-team@example.com" if follow_up_status != "Pending" else "",
            "llmProcessed": True,
            "ttl": ttl,
        }
        events.append(event)

    return events


def main() -> None:
    table_name = sys.argv[1] if len(sys.argv) > 1 else TABLE_NAME
    print(f"Seeding {table_name} with 50 mock events...")
    table = dynamodb.Table(table_name)

    events = generate_events()
    with table.batch_writer() as batch:
        for event in events:
            batch.put_item(Item=event)

    print(f"Successfully inserted {len(events)} events into {table_name}")


if __name__ == "__main__":
    main()
