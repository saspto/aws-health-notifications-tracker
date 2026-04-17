import base64
import json
import os
import logging
from typing import Any
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "HealthEvents")
REGION = os.environ.get("REGION", "us-east-1")

dynamodb = boto3.resource("dynamodb", region_name=REGION)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,PATCH,OPTIONS",
    "Content-Type": "application/json",
}

VALID_FOLLOW_UP_STATUSES = {"Pending", "In Progress", "Resolved"}


def resp(status: int, body: Any) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": CORS_HEADERS,
        "body": json.dumps(body, default=str),
    }


def list_events(table: Any, qp: dict[str, str]) -> dict[str, Any]:
    limit = int(qp.get("limit", "25"))
    last_key_enc = qp.get("lastKey")
    service_filter = qp.get("service")
    urgency_filter = qp.get("urgency")
    status_filter = qp.get("status")
    search = qp.get("search", "").lower()

    scan_kwargs: dict[str, Any] = {"Limit": limit}

    if last_key_enc:
        try:
            scan_kwargs["ExclusiveStartKey"] = json.loads(base64.b64decode(last_key_enc))
        except Exception:
            pass

    filter_parts = [Attr("accountId").ne("system")]

    if service_filter:
        filter_parts.append(Attr("service").eq(service_filter))
    if urgency_filter:
        filter_parts.append(Attr("urgency").eq(urgency_filter))
    if status_filter:
        filter_parts.append(Attr("status").eq(status_filter))

    if len(filter_parts) == 1:
        scan_kwargs["FilterExpression"] = filter_parts[0]
    elif len(filter_parts) > 1:
        expr = filter_parts[0]
        for part in filter_parts[1:]:
            expr = expr & part
        scan_kwargs["FilterExpression"] = expr

    response = table.scan(**scan_kwargs)
    items = response.get("Items", [])

    if search:
        items = [
            i for i in items
            if search in i.get("summary", "").lower()
            or search in i.get("eventTypeCode", "").lower()
            or search in i.get("service", "").lower()
        ]

    next_key = None
    if response.get("LastEvaluatedKey"):
        next_key = base64.b64encode(json.dumps(response["LastEvaluatedKey"]).encode()).decode()

    return {"items": items, "nextKey": next_key, "count": len(items)}


def get_event(table: Any, event_arn: str, account_id: str) -> dict[str, Any] | None:
    try:
        response = table.get_item(Key={"eventArn": event_arn, "accountId": account_id})
        return response.get("Item")
    except ClientError:
        return None


def patch_event(table: Any, event_arn: str, account_id: str, body: dict[str, Any]) -> dict[str, Any]:
    follow_up_status = body.get("followUpStatus")
    if follow_up_status and follow_up_status not in VALID_FOLLOW_UP_STATUSES:
        raise ValueError(f"Invalid followUpStatus: {follow_up_status}")

    update_expr_parts = ["lastUpdated = :t"]
    expr_values: dict[str, Any] = {":t": datetime.now(timezone.utc).isoformat()}

    if follow_up_status:
        update_expr_parts.append("followUpStatus = :fs")
        expr_values[":fs"] = follow_up_status
    if "followUpNotes" in body:
        update_expr_parts.append("followUpNotes = :fn")
        expr_values[":fn"] = body["followUpNotes"]
    if "followUpOwner" in body:
        update_expr_parts.append("followUpOwner = :fo")
        expr_values[":fo"] = body["followUpOwner"]

    table.update_item(
        Key={"eventArn": event_arn, "accountId": account_id},
        UpdateExpression="SET " + ", ".join(update_expr_parts),
        ExpressionAttributeValues=expr_values,
    )
    return {"updated": True}


def get_stats(table: Any) -> dict[str, Any]:
    response = table.scan(FilterExpression=Attr("accountId").ne("system"))
    items = response.get("Items", [])

    now = datetime.now(timezone.utc)
    from datetime import timedelta
    week_from_now = (now + timedelta(days=7)).isoformat()

    stats: dict[str, Any] = {
        "total": 0,
        "byUrgency": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        "byStatus": {},
        "byService": {},
        "upcomingDeadlines": 0,
        "pendingFollowUps": 0,
    }

    for item in items:
        if item.get("eventArn", "").startswith("cursor/"):
            continue
        stats["total"] += 1
        urgency = item.get("urgency", "Low")
        if urgency in stats["byUrgency"]:
            stats["byUrgency"][urgency] += 1

        status = item.get("status", "Unknown")
        stats["byStatus"][status] = stats["byStatus"].get(status, 0) + 1

        service = item.get("service", "Unknown")
        stats["byService"][service] = stats["byService"].get(service, 0) + 1

        deadline = item.get("deadline", "")
        if deadline and now.isoformat() <= deadline <= week_from_now:
            stats["upcomingDeadlines"] += 1

        if item.get("followUpStatus") == "Pending":
            stats["pendingFollowUps"] += 1

    top_services = sorted(stats["byService"].items(), key=lambda x: x[1], reverse=True)[:10]
    stats["byService"] = dict(top_services)

    return stats


def get_accounts(table: Any) -> list[dict[str, Any]]:
    response = table.scan(
        FilterExpression=Attr("accountId").ne("system"),
        ProjectionExpression="accountId, accountAlias",
    )
    seen: dict[str, str] = {}
    for item in response.get("Items", []):
        acc_id = item.get("accountId", "")
        if acc_id and not acc_id.startswith("cursor"):
            seen[acc_id] = item.get("accountAlias", "")
    return [{"accountId": k, "accountAlias": v} for k, v in sorted(seen.items())]


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    table = dynamodb.Table(TABLE_NAME)
    method = event.get("requestContext", {}).get("http", {}).get("method", "GET")
    raw_path = event.get("rawPath", "")
    path_params = event.get("pathParameters") or {}
    qp = event.get("queryStringParameters") or {}

    if method == "OPTIONS":
        return resp(200, {})

    try:
        if method == "GET" and raw_path == "/events":
            return resp(200, list_events(table, qp))

        elif method == "GET" and "/events/" in raw_path:
            # rawPath: /events/<eventArn>/<accountId> — accountId is last segment
            after_prefix = raw_path[len("/events/"):]
            account_id = after_prefix.rsplit("/", 1)[-1]
            event_arn = after_prefix.rsplit("/", 1)[0]
            item = get_event(table, event_arn, account_id)
            if item is None:
                return resp(404, {"error": "Event not found"})
            return resp(200, item)

        elif method == "PATCH" and "/events/" in raw_path:
            after_prefix = raw_path[len("/events/"):]
            account_id = after_prefix.rsplit("/", 1)[-1]
            event_arn = after_prefix.rsplit("/", 1)[0]
            body_str = event.get("body", "{}")
            body = json.loads(body_str) if body_str else {}
            try:
                result = patch_event(table, event_arn, account_id, body)
                return resp(200, result)
            except ValueError as e:
                return resp(400, {"error": str(e)})

        elif method == "GET" and raw_path == "/stats":
            return resp(200, get_stats(table))

        elif method == "GET" and raw_path == "/accounts":
            return resp(200, get_accounts(table))

        return resp(404, {"error": "Not found"})

    except Exception as e:
        logger.error("Error handling request: %s", e)
        return resp(500, {"error": "Internal server error"})
