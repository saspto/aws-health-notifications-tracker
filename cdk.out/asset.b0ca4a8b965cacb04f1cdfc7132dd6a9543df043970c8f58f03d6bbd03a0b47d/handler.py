import json
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "HealthEvents")
ARCHIVE_BUCKET = os.environ.get("ARCHIVE_BUCKET", "")
REGION = os.environ.get("REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)
s3_client = boto3.client("s3", region_name=REGION)
health_client = boto3.client("health", region_name="us-east-1", endpoint_url="https://health.us-east-1.amazonaws.com")


def get_last_run_time(table: Any) -> str:
    try:
        response = table.get_item(Key={"eventArn": "cursor/last_run_time", "accountId": "system"})
        return response.get("Item", {}).get("value", "")
    except ClientError:
        return ""


def update_cursor(table: Any, key: str, value: str) -> None:
    table.put_item(
        Item={
            "eventArn": f"cursor/{key}",
            "accountId": "system",
            "value": value,
            "lastUpdated": datetime.now(timezone.utc).isoformat(),
        }
    )


def fetch_org_events(start_time: datetime, end_time: datetime) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    paginator = health_client.get_paginator("describe_events_for_organization")
    filter_params: dict[str, Any] = {
        "filter": {
            "lastUpdatedTime": {
                "from": start_time.isoformat(),
                "to": end_time.isoformat(),
            }
        }
    }
    for page in paginator.paginate(**filter_params):
        events.extend(page.get("events", []))
    return events


def get_event_details(event_arns: list[str]) -> dict[str, Any]:
    details: dict[str, Any] = {}
    for i in range(0, len(event_arns), 10):
        batch = event_arns[i : i + 10]
        try:
            response = health_client.describe_event_details_for_organization(
                organizationEventDetailFilters=[{"eventArn": arn} for arn in batch]
            )
            for detail in response.get("successfulSet", []):
                event = detail.get("event", {})
                arn = event.get("arn", "")
                details[arn] = {
                    "event": event,
                    "description": detail.get("eventDescription", {}).get("latestDescription", ""),
                }
        except ClientError as e:
            logger.error("Error fetching event details: %s", e)
    return details


def get_affected_accounts(event_arn: str) -> list[str]:
    accounts: list[str] = []
    try:
        paginator = health_client.get_paginator("describe_affected_accounts_for_organization_event")
        for page in paginator.paginate(eventArn=event_arn):
            accounts.extend(page.get("affectedAccounts", []))
    except ClientError as e:
        logger.error("Error fetching affected accounts for %s: %s", event_arn, e)
    return accounts


def upsert_event(table: Any, event: dict[str, Any], account_id: str, description: str) -> None:
    now = datetime.now(timezone.utc)
    arn = event.get("arn", "")
    end_time = event.get("endTime")
    ttl_time = int((end_time + timedelta(days=365)).timestamp()) if end_time else int((now + timedelta(days=365)).timestamp())

    item = {
        "eventArn": arn,
        "accountId": account_id,
        "service": event.get("service", ""),
        "eventTypeCode": event.get("eventTypeCode", ""),
        "eventTypeCategory": event.get("eventTypeCategory", ""),
        "region": event.get("region", ""),
        "startTime": event.get("startTime", now).isoformat() if hasattr(event.get("startTime", now), "isoformat") else str(event.get("startTime", "")),
        "endTime": end_time.isoformat() if end_time and hasattr(end_time, "isoformat") else str(end_time or ""),
        "lastUpdated": now.isoformat(),
        "statusCode": event.get("statusCode", "open"),
        "status": event.get("statusCode", "open").capitalize(),
        "rawDescription": description,
        "llmProcessed": False,
        "followUpStatus": "Pending",
        "followUpNotes": "",
        "followUpOwner": "",
        "urgency": "Low",
        "summary": "",
        "recommendedActions": [],
        "deadline": "",
        "affectedResources": [],
        "ttl": ttl_time,
    }

    table.put_item(Item=item)


def archive_to_s3(event_arn: str, account_id: str, data: dict[str, Any]) -> None:
    if not ARCHIVE_BUCKET:
        return
    now = datetime.now(timezone.utc)
    safe_arn = event_arn.replace(":", "_").replace("/", "_")
    key = f"raw/{now.year}/{now.month:02d}/{now.day:02d}/{safe_arn}_{account_id}.json"
    try:
        s3_client.put_object(
            Bucket=ARCHIVE_BUCKET,
            Key=key,
            Body=json.dumps(data, default=str),
            ContentType="application/json",
        )
    except ClientError as e:
        logger.error("Error archiving to S3: %s", e)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    table = dynamodb.Table(TABLE_NAME)
    now = datetime.now(timezone.utc)

    last_run_str = get_last_run_time(table)
    if last_run_str:
        try:
            start_time = datetime.fromisoformat(last_run_str.replace("Z", "+00:00"))
        except ValueError:
            start_time = now - timedelta(minutes=15)
    else:
        start_time = now - timedelta(minutes=15)

    try:
        events = fetch_org_events(start_time, now)
        logger.info("Fetched %d events", len(events))

        if not events:
            logger.info("No events found in time window")
            update_cursor(table, "last_run_time", now.isoformat())
            return {"statusCode": 200, "body": "No events"}

        event_arns = [e.get("arn", "") for e in events if e.get("arn")]
        details_map = get_event_details(event_arns)

        for evt in events:
            arn = evt.get("arn", "")
            affected_accounts = get_affected_accounts(arn)
            detail_info = details_map.get(arn, {})
            description = detail_info.get("description", "")

            if not affected_accounts:
                affected_accounts = ["unknown"]

            for acc_id in affected_accounts:
                upsert_event(table, evt, acc_id, description)
                archive_to_s3(arn, acc_id, {"event": evt, "description": description, "accountId": acc_id})

        update_cursor(table, "last_run_time", now.isoformat())
        return {"statusCode": 200, "body": f"Processed {len(events)} events"}

    except Exception as e:
        logger.error("Error in health_collector: %s", e)
        raise
