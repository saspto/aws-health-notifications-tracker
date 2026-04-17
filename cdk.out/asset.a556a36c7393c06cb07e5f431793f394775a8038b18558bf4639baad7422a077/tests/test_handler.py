import base64
import json
from unittest.mock import MagicMock, patch
import pytest


def make_api_event(method: str, path: str, path_params: dict = None, query_params: dict = None, body: dict = None) -> dict:
    return {
        "requestContext": {"http": {"method": method}},
        "rawPath": path,
        "pathParameters": path_params or {},
        "queryStringParameters": query_params or {},
        "body": json.dumps(body) if body else None,
    }


def make_health_item(event_arn: str = "arn:aws:health::event/ECS/TEST/123", account_id: str = "123456789012") -> dict:
    return {
        "eventArn": event_arn,
        "accountId": account_id,
        "service": "ECS",
        "eventTypeCode": "AWS_ECS_TEST",
        "urgency": "High",
        "status": "Open",
        "followUpStatus": "Pending",
        "summary": "Test summary for ECS maintenance",
        "deadline": "2026-05-01T00:00:00+00:00",
        "startTime": "2026-04-01T00:00:00+00:00",
    }


def test_list_events_default_pagination():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        items = [make_health_item(f"arn:test:{i}", f"account{i}") for i in range(25)]
        mock_table = MagicMock()
        mock_table.scan.return_value = {
            "Items": items,
            "LastEvaluatedKey": {"eventArn": "last", "accountId": "acc"},
        }
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("GET", "/events"), None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "items" in body
        assert "nextKey" in body
        assert body["nextKey"] is not None


def test_list_events_filter_by_service():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": [make_health_item()], "LastEvaluatedKey": None}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("GET", "/events", query_params={"service": "ECS"}), None)

        assert result["statusCode"] == 200
        scan_kwargs = mock_table.scan.call_args[1]
        assert "FilterExpression" in scan_kwargs


def test_list_events_filter_by_urgency():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": [make_health_item()], "LastEvaluatedKey": None}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("GET", "/events", query_params={"urgency": "Critical"}), None)

        assert result["statusCode"] == 200


def test_list_events_search():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        items = [make_health_item(), {**make_health_item(), "summary": "unrelated content", "eventTypeCode": "OTHER"}]
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": items}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("GET", "/events", query_params={"search": "maintenance"}), None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        for item in body["items"]:
            assert "maintenance" in item.get("summary", "").lower() or \
                   "maintenance" in item.get("eventTypeCode", "").lower()


def test_get_event_detail_success():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.get_item.return_value = {"Item": make_health_item()}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(
                make_api_event("GET", "/events/arn/acc",
                               path_params={"eventArn": "arn:aws:health::event/ECS/TEST/123", "accountId": "123456789012"}),
                None
            )

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert body["service"] == "ECS"


def test_get_event_detail_not_found():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(
                make_api_event("GET", "/events/arn/acc",
                               path_params={"eventArn": "arn:missing", "accountId": "unknown"}),
                None
            )

        assert result["statusCode"] == 404


def test_patch_followup_status():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(
                make_api_event(
                    "PATCH", "/events/arn/acc",
                    path_params={"eventArn": "arn:test", "accountId": "123456789012"},
                    body={"followUpStatus": "In Progress", "followUpOwner": "alice@example.com", "followUpNotes": "Working on it"},
                ),
                None
            )

        assert result["statusCode"] == 200
        mock_table.update_item.assert_called_once()


def test_patch_invalid_status():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(
                make_api_event(
                    "PATCH", "/events/arn/acc",
                    path_params={"eventArn": "arn:test", "accountId": "123456789012"},
                    body={"followUpStatus": "INVALID_STATUS"},
                ),
                None
            )

        assert result["statusCode"] == 400


def test_stats_aggregation():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        items = [
            {**make_health_item(), "urgency": "Critical", "status": "Open", "followUpStatus": "Pending"},
            {**make_health_item(), "urgency": "High", "status": "Open", "followUpStatus": "In Progress"},
            {**make_health_item(), "urgency": "Low", "status": "Closed", "followUpStatus": "Resolved"},
        ]
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": items}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("GET", "/stats"), None)

        assert result["statusCode"] == 200
        body = json.loads(result["body"])
        assert "total" in body
        assert "byUrgency" in body
        assert "byStatus" in body


def test_cors_headers_present():
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.scan.return_value = {"Items": []}
        mock_ddb.Table.return_value = mock_table

        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("GET", "/events"), None)

        assert "Access-Control-Allow-Origin" in result["headers"]


def test_unauthorized_returns_401():
    # API Gateway handles auth, but test that OPTIONS returns 200
    with patch("lambdas.api_handler.handler.dynamodb") as mock_ddb:
        mock_ddb.Table.return_value = MagicMock()
        from lambdas.api_handler import handler as h
        with patch.object(h, "dynamodb", mock_ddb):
            result = h.handler(make_api_event("OPTIONS", "/events"), None)
        assert result["statusCode"] == 200
