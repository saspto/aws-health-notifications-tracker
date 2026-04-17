"""Integration tests — require real AWS resources to be deployed."""
import json
import os
from unittest.mock import MagicMock, patch
import pytest

TABLE_NAME = os.environ.get("TABLE_NAME", "HealthEvents")


@pytest.mark.integration
def test_health_collector_to_dynamodb():
    mock_events = [
        {
            "arn": "arn:aws:health:us-east-1::event/ECS/AWS_ECS_MAINTENANCE/TEST001",
            "service": "ECS",
            "eventTypeCode": "AWS_ECS_MAINTENANCE_SCHEDULED",
            "eventTypeCategory": "scheduledChange",
            "region": "us-east-1",
            "statusCode": "open",
        }
    ]
    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb, \
         patch("lambdas.health_collector.handler.s3_client"):
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"events": mock_events}]
        mock_affected_paginator = MagicMock()
        mock_affected_paginator.paginate.return_value = [{"affectedAccounts": ["123456789012"]}]
        mock_health.get_paginator.side_effect = lambda name: (
            mock_paginator if name == "describe_events_for_organization" else mock_affected_paginator
        )
        mock_health.describe_event_details_for_organization.return_value = {
            "successfulSet": [{"event": mock_events[0], "eventDescription": {"latestDescription": "Test"}}]
        }
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_ddb.Table.return_value = mock_table

        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), patch.object(h, "health_client", mock_health):
            result = h.handler({}, None)

        assert result["statusCode"] == 200
        mock_table.put_item.assert_called()


@pytest.mark.integration
def test_dynamodb_stream_triggers_summarizer():
    stream_record = {
        "Records": [
            {
                "eventName": "INSERT",
                "dynamodb": {
                    "NewImage": {
                        "eventArn": {"S": "arn:aws:health::event/ECS/TEST/001"},
                        "accountId": {"S": "123456789012"},
                        "service": {"S": "ECS"},
                        "eventTypeCode": {"S": "AWS_ECS_MAINTENANCE"},
                        "startTime": {"S": "2026-04-01T00:00:00+00:00"},
                        "endTime": {"S": "2026-05-01T00:00:00+00:00"},
                        "rawDescription": {"S": "Test maintenance"},
                        "llmProcessed": {"BOOL": False},
                    }
                },
            }
        ]
    }

    import json as _json
    llm_response = _json.dumps({
        "summary": "Test summary",
        "recommendedActions": ["Action 1"],
        "urgency": "High",
        "deadline": "2026-05-01T00:00:00Z",
    })

    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        body_mock = MagicMock()
        body_mock.read.return_value = _json.dumps({"content": [{"text": llm_response}]}).encode()
        mock_bedrock.invoke_model.return_value = {"body": body_mock}
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(stream_record, None)

        assert result["statusCode"] == 200
        mock_table.update_item.assert_called_once()
        args = mock_table.update_item.call_args[1]
        assert args["ExpressionAttributeValues"][":p"] is True


@pytest.mark.integration
def test_api_list_and_filter():
    items = [
        {"eventArn": "arn:test:1", "accountId": "123", "service": "ECS", "urgency": "High",
         "status": "Open", "followUpStatus": "Pending", "summary": "ECS maintenance"},
        {"eventArn": "arn:test:2", "accountId": "456", "service": "RDS", "urgency": "Low",
         "status": "Open", "followUpStatus": "Resolved", "summary": "RDS update"},
    ]

    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": items}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(
                {
                    "requestContext": {"http": {"method": "GET"}},
                    "rawPath": "/events",
                    "pathParameters": {},
                    "queryStringParameters": {"service": "ECS"},
                    "body": None,
                },
                None,
            )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "items" in body


@pytest.mark.integration
def test_full_pipeline():
    """End-to-end: health collector → stream → summarizer → API."""
    import json as _json

    # Step 1: collect
    collected_items = []

    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb, \
         patch("lambdas.health_collector.handler.s3_client"):
        mock_event = {
            "arn": "arn:aws:health::event/ECS/TEST/FULL",
            "service": "ECS",
            "eventTypeCode": "AWS_ECS_MAINTENANCE",
            "statusCode": "open",
        }
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"events": [mock_event]}]
        mock_affected_paginator = MagicMock()
        mock_affected_paginator.paginate.return_value = [{"affectedAccounts": ["123456789012"]}]
        mock_health.get_paginator.side_effect = lambda name: (
            mock_paginator if name == "describe_events_for_organization" else mock_affected_paginator
        )
        mock_health.describe_event_details_for_organization.return_value = {
            "successfulSet": [{"event": mock_event, "eventDescription": {"latestDescription": "desc"}}]
        }

        def capture_put(Item: dict) -> dict:
            collected_items.append(Item)
            return {}

        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_table.put_item.side_effect = capture_put
        mock_ddb.Table.return_value = mock_table

        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), patch.object(h, "health_client", mock_health):
            h.handler({}, None)

    assert len(collected_items) >= 1

    # Step 2: summarize via stream
    llm_json = _json.dumps({
        "summary": "Pipeline test summary",
        "recommendedActions": ["Test action"],
        "urgency": "High",
        "deadline": "2026-05-01T00:00:00Z",
    })

    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb2:
        body_mock = MagicMock()
        body_mock.read.return_value = _json.dumps({"content": [{"text": llm_json}]}).encode()
        mock_bedrock.invoke_model.return_value = {"body": body_mock}
        mock_table2 = MagicMock()
        mock_ddb2.Table.return_value = mock_table2

        stream_record = {
            "Records": [
                {
                    "eventName": "INSERT",
                    "dynamodb": {
                        "NewImage": {
                            "eventArn": {"S": "arn:aws:health::event/ECS/TEST/FULL"},
                            "accountId": {"S": "123456789012"},
                            "service": {"S": "ECS"},
                            "eventTypeCode": {"S": "AWS_ECS_MAINTENANCE"},
                            "startTime": {"S": "2026-04-01T00:00:00+00:00"},
                            "endTime": {"S": "2026-05-01T00:00:00+00:00"},
                            "rawDescription": {"S": "desc"},
                            "llmProcessed": {"BOOL": False},
                        }
                    },
                }
            ]
        }

        from lambdas.llm_summarizer import handler as h2
        with patch.object(h2, "bedrock_client", mock_bedrock), patch.object(h2, "dynamodb", mock_ddb2):
            result = h2.handler(stream_record, None)

        assert result["statusCode"] == 200
        mock_table2.update_item.assert_called_once()
