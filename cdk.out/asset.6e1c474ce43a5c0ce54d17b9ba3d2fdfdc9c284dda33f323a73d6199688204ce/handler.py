import json
import os
import logging
import re
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

TABLE_NAME = os.environ.get("TABLE_NAME", "HealthEvents")
REGION = os.environ.get("REGION", "us-east-1")
BEDROCK_MODEL_ID = "anthropic.claude-haiku-4-5-20251001"

dynamodb = boto3.resource("dynamodb", region_name=REGION)
bedrock_client = boto3.client("bedrock-runtime", region_name=REGION)


def build_prompt(service: str, event_type_code: str, start_time: str, end_time: str, description: str) -> str:
    return f"""You are an AWS cloud operations assistant. Given this AWS Health event, provide:
1. A 2-3 sentence plain-English summary for a non-technical stakeholder
2. A bulleted list of 3-5 specific recommended actions with clear steps
3. Urgency classification: Critical (deadline <3 days), High (deadline 4-14 days), Medium (deadline 15-30 days), Low (deadline >30 days or no deadline)
4. Extract the action deadline date in ISO 8601 format (or null if none)

Respond ONLY as valid JSON: {{"summary": "...", "recommendedActions": ["...", "..."], "urgency": "High", "deadline": "2026-05-01T00:00:00Z"}}

AWS Health Event:
Service: {service}
Event Type: {event_type_code}
Start: {start_time}
End: {end_time}
Description: {description}"""


def invoke_bedrock(prompt: str, max_retries: int = 2) -> dict[str, Any]:
    for attempt in range(max_retries + 1):
        try:
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            }
            response = bedrock_client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            response_body = json.loads(response["body"].read())
            content = response_body["content"][0]["text"]

            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())

            raise ValueError(f"No valid JSON in response: {content}")

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning("Attempt %d failed to parse LLM response: %s", attempt + 1, e)
            if attempt == max_retries:
                raise
    return {}


def update_dynamodb(table: Any, event_arn: str, account_id: str, llm_result: dict[str, Any]) -> None:
    table.update_item(
        Key={"eventArn": event_arn, "accountId": account_id},
        UpdateExpression="SET summary = :s, recommendedActions = :r, urgency = :u, deadline = :d, llmProcessed = :p, lastUpdated = :t",
        ExpressionAttributeValues={
            ":s": llm_result.get("summary", ""),
            ":r": llm_result.get("recommendedActions", []),
            ":u": llm_result.get("urgency", "Low"),
            ":d": llm_result.get("deadline") or "",
            ":p": True,
            ":t": datetime.now(timezone.utc).isoformat(),
        },
    )


def process_record(table: Any, record: dict[str, Any]) -> None:
    if record.get("eventName") not in ("INSERT", "MODIFY"):
        return

    new_image = record.get("dynamodb", {}).get("NewImage", {})

    if new_image.get("llmProcessed", {}).get("BOOL", False):
        return

    event_arn = new_image.get("eventArn", {}).get("S", "")
    account_id = new_image.get("accountId", {}).get("S", "")

    if not event_arn or event_arn.startswith("cursor/"):
        return

    service = new_image.get("service", {}).get("S", "")
    event_type_code = new_image.get("eventTypeCode", {}).get("S", "")
    start_time = new_image.get("startTime", {}).get("S", "")
    end_time = new_image.get("endTime", {}).get("S", "")
    description = new_image.get("rawDescription", {}).get("S", "")

    prompt = build_prompt(service, event_type_code, start_time, end_time, description)

    try:
        llm_result = invoke_bedrock(prompt)
        update_dynamodb(table, event_arn, account_id, llm_result)
        logger.info("Processed event %s for account %s", event_arn, account_id)
    except Exception as e:
        logger.error("Error processing event %s: %s", event_arn, e)
        raise


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    table = dynamodb.Table(TABLE_NAME)
    records = event.get("Records", [])
    logger.info("Processing %d records", len(records))

    for record in records:
        process_record(table, record)

    return {"statusCode": 200, "body": f"Processed {len(records)} records"}
