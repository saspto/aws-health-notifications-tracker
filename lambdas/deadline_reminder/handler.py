import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "HealthEvents")
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")
REGION = os.environ.get("REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
sns_client = boto3.client("sns", region_name=REGION)
cloudwatch_client = boto3.client("cloudwatch", region_name=REGION)


def query_upcoming_deadlines(table: Any) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    upcoming: list[dict[str, Any]] = []

    for urgency in ["Critical", "High"]:
        window_end = now + timedelta(days=7)
        try:
            response = table.query(
                IndexName="GSI2",
                KeyConditionExpression=Key("urgency").eq(urgency)
                & Key("deadline").between(now.isoformat(), window_end.isoformat()),
                FilterExpression=Attr("followUpStatus").ne("Resolved"),
            )
            upcoming.extend(response.get("Items", []))
        except Exception as e:
            logger.error("Error querying GSI2 for %s: %s", urgency, e)

    medium_end = now + timedelta(days=3)
    try:
        response = table.query(
            IndexName="GSI2",
            KeyConditionExpression=Key("urgency").eq("Medium")
            & Key("deadline").between(now.isoformat(), medium_end.isoformat()),
            FilterExpression=Attr("followUpStatus").ne("Resolved"),
        )
        upcoming.extend(response.get("Items", []))
    except Exception as e:
        logger.error("Error querying GSI2 for Medium: %s", e)

    return upcoming


def build_digest(events: list[dict[str, Any]]) -> str:
    by_account: dict[str, list[dict[str, Any]]] = {}
    for evt in events:
        acc = evt.get("accountId", "unknown")
        by_account.setdefault(acc, []).append(evt)

    lines = ["AWS Health Deadline Reminder\n", "=" * 40]
    for acc, evts in sorted(by_account.items()):
        lines.append(f"\nAccount: {acc}")
        for e in evts:
            lines.append(f"  - [{e.get('urgency', 'Unknown')}] {e.get('eventTypeCode', 'Unknown')} | Deadline: {e.get('deadline', 'N/A')} | Status: {e.get('followUpStatus', 'Pending')}")
            if e.get("summary"):
                lines.append(f"    Summary: {e.get('summary', '')[:200]}")

    return "\n".join(lines)


def publish_metric(count: int) -> None:
    try:
        cloudwatch_client.put_metric_data(
            Namespace="HealthTracker",
            MetricData=[
                {
                    "MetricName": "RemindersPublished",
                    "Value": float(count),
                    "Unit": "Count",
                    "Timestamp": datetime.now(timezone.utc),
                }
            ],
        )
    except Exception as e:
        logger.error("Error publishing metric: %s", e)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    table = dynamodb.Table(TABLE_NAME)

    upcoming = query_upcoming_deadlines(table)
    logger.info("Found %d events with upcoming deadlines", len(upcoming))

    if not upcoming:
        publish_metric(0)
        return {"statusCode": 200, "body": "No upcoming deadlines"}

    digest = build_digest(upcoming)

    if SNS_TOPIC_ARN:
        try:
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"AWS Health Deadline Alert - {len(upcoming)} events require attention",
                Message=json.dumps(
                    {
                        "default": digest,
                        "email": digest,
                        "eventCount": len(upcoming),
                        "generatedAt": datetime.now(timezone.utc).isoformat(),
                    }
                ),
                MessageStructure="json",
            )
            logger.info("Published SNS notification for %d events", len(upcoming))
        except Exception as e:
            logger.error("Error publishing to SNS: %s", e)

    publish_metric(len(upcoming))
    return {"statusCode": 200, "body": f"Published reminders for {len(upcoming)} events"}
