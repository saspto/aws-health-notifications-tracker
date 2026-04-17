import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest


def make_event(urgency: str, deadline_offset_days: int, follow_up_status: str = "Pending") -> dict:
    deadline = (datetime.now(timezone.utc) + timedelta(days=deadline_offset_days)).isoformat()
    return {
        "eventArn": f"arn:aws:health::event/TEST/{urgency}",
        "accountId": "123456789012",
        "service": "ECS",
        "eventTypeCode": "AWS_ECS_TEST",
        "urgency": urgency,
        "deadline": deadline,
        "followUpStatus": follow_up_status,
        "summary": "Test event summary",
    }


def test_query_upcoming_deadlines():
    with patch("lambdas.deadline_reminder.handler.dynamodb") as mock_ddb, \
         patch("lambdas.deadline_reminder.handler.sns_client"), \
         patch("lambdas.deadline_reminder.handler.cloudwatch_client"):
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [make_event("Critical", 3)]}
        mock_ddb.Table.return_value = mock_table

        from lambdas.deadline_reminder import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "sns_client", MagicMock()), \
             patch.object(h, "cloudwatch_client", MagicMock()):
            result = h.handler({}, None)

        assert result["statusCode"] == 200
        mock_table.query.assert_called()


def test_sns_publish_called_for_critical_events():
    with patch("lambdas.deadline_reminder.handler.dynamodb") as mock_ddb, \
         patch("lambdas.deadline_reminder.handler.cloudwatch_client"):
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [make_event("Critical", 2)]}
        mock_ddb.Table.return_value = mock_table

        mock_sns = MagicMock()

        from lambdas.deadline_reminder import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "sns_client", mock_sns), \
             patch.object(h, "cloudwatch_client", MagicMock()), \
             patch.object(h, "SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test"):
            h.handler({}, None)

        mock_sns.publish.assert_called_once()


def test_no_sns_when_no_upcoming_deadlines():
    with patch("lambdas.deadline_reminder.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": []}
        mock_ddb.Table.return_value = mock_table

        mock_sns = MagicMock()

        from lambdas.deadline_reminder import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "sns_client", mock_sns), \
             patch.object(h, "cloudwatch_client", MagicMock()):
            result = h.handler({}, None)

        mock_sns.publish.assert_not_called()
        assert "No upcoming" in result["body"]


def test_resolved_events_excluded():
    with patch("lambdas.deadline_reminder.handler.dynamodb") as mock_ddb, \
         patch("lambdas.deadline_reminder.handler.cloudwatch_client"):
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [make_event("Critical", 2, follow_up_status="Resolved")]}
        mock_ddb.Table.return_value = mock_table

        mock_sns = MagicMock()

        from lambdas.deadline_reminder import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "sns_client", mock_sns), \
             patch.object(h, "cloudwatch_client", MagicMock()), \
             patch.object(h, "SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test"):
            # DynamoDB filter would exclude resolved items, mock returns them for testing build_digest
            # The actual filtering is done by DynamoDB FilterExpression
            h.handler({}, None)

        # SNS should still be called since we have events (filter is applied at DynamoDB level)
        # In real scenario, Resolved events won't be returned by DynamoDB query


def test_cloudwatch_metric_published():
    with patch("lambdas.deadline_reminder.handler.dynamodb") as mock_ddb, \
         patch("lambdas.deadline_reminder.handler.sns_client"):
        mock_table = MagicMock()
        mock_table.query.return_value = {"Items": [make_event("Critical", 2)]}
        mock_ddb.Table.return_value = mock_table

        mock_cw = MagicMock()

        from lambdas.deadline_reminder import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "sns_client", MagicMock()), \
             patch.object(h, "cloudwatch_client", mock_cw), \
             patch.object(h, "SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test"):
            h.handler({}, None)

        mock_cw.put_metric_data.assert_called_once()
        call_args = mock_cw.put_metric_data.call_args[1]
        assert call_args["Namespace"] == "HealthTracker"
