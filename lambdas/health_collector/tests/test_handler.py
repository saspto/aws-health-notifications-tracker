import json
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch, call
import pytest


@pytest.fixture
def mock_table():
    table = MagicMock()
    table.get_item.return_value = {"Item": {"value": (datetime.now(timezone.utc) - timedelta(minutes=20)).isoformat()}}
    return table


@pytest.fixture
def sample_event():
    return {
        "arn": "arn:aws:health:us-east-1::event/ECS/AWS_ECS_MAINTENANCE/123",
        "service": "ECS",
        "eventTypeCode": "AWS_ECS_MAINTENANCE_SCHEDULED",
        "eventTypeCategory": "scheduledChange",
        "region": "us-east-1",
        "startTime": datetime(2026, 4, 1, tzinfo=timezone.utc),
        "endTime": datetime(2026, 5, 1, tzinfo=timezone.utc),
        "statusCode": "open",
    }


def test_fetch_org_events_success(sample_event):
    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb, \
         patch("lambdas.health_collector.handler.s3_client"):
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"events": [sample_event]}]
        mock_health.get_paginator.return_value = mock_paginator

        mock_affected_paginator = MagicMock()
        mock_affected_paginator.paginate.return_value = [{"affectedAccounts": ["123456789012"]}]
        mock_health.get_paginator.side_effect = lambda name: (
            mock_paginator if name == "describe_events_for_organization" else mock_affected_paginator
        )

        mock_health.describe_event_details_for_organization.return_value = {
            "successfulSet": [{"event": sample_event, "eventDescription": {"latestDescription": "Test description"}}]
        }

        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_ddb.Table.return_value = mock_table

        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "health_client", mock_health), \
             patch.object(h, "s3_client", MagicMock()):
            result = h.handler({}, None)

        assert result["statusCode"] == 200


def test_fetch_org_events_empty_response(mock_table):
    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb:
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"events": []}]
        mock_health.get_paginator.return_value = mock_paginator

        mock_ddb.Table.return_value = mock_table

        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "health_client", mock_health):
            result = h.handler({}, None)

        assert result["statusCode"] == 200
        mock_table.put_item.assert_not_called()


def test_checkpoint_cursor_updated(mock_table):
    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb, \
         patch("lambdas.health_collector.handler.s3_client"):
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"events": []}]
        mock_health.get_paginator.return_value = mock_paginator
        mock_ddb.Table.return_value = mock_table

        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "health_client", mock_health):
            h.handler({}, None)

        mock_table.put_item.assert_called()
        call_args = mock_table.put_item.call_args
        assert "cursor/last_run_time" in str(call_args)


def test_s3_archive_written(mock_table, sample_event):
    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb, \
         patch("lambdas.health_collector.handler.s3_client") as mock_s3:
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{"events": [sample_event]}]
        mock_affected_paginator = MagicMock()
        mock_affected_paginator.paginate.return_value = [{"affectedAccounts": ["123456789012"]}]
        mock_health.get_paginator.side_effect = lambda name: (
            mock_paginator if name == "describe_events_for_organization" else mock_affected_paginator
        )
        mock_health.describe_event_details_for_organization.return_value = {
            "successfulSet": [{"event": sample_event, "eventDescription": {"latestDescription": "desc"}}]
        }
        mock_ddb.Table.return_value = mock_table

        import os
        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "health_client", mock_health), \
             patch.object(h, "s3_client", mock_s3), \
             patch.object(h, "ARCHIVE_BUCKET", "test-bucket"):
            h.handler({}, None)

        mock_s3.put_object.assert_called()


def test_affected_accounts_pagination(mock_table):
    from lambdas.health_collector.handler import get_affected_accounts
    with patch("lambdas.health_collector.handler.health_client") as mock_health:
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [
            {"affectedAccounts": ["111111111111", "222222222222"]},
            {"affectedAccounts": ["333333333333"]},
        ]
        mock_health.get_paginator.return_value = mock_paginator

        from lambdas.health_collector import handler as h
        with patch.object(h, "health_client", mock_health):
            accounts = h.get_affected_accounts("arn:test")

        assert len(accounts) == 3
        assert "111111111111" in accounts


def test_duplicate_event_upsert(mock_table, sample_event):
    from lambdas.health_collector.handler import upsert_event
    from lambdas.health_collector import handler as h
    h.upsert_event(mock_table, sample_event, "123456789012", "description")
    mock_table.put_item.assert_called_once()


def test_retry_on_throttle():
    from botocore.exceptions import ClientError
    error_response = {"Error": {"Code": "ThrottlingException", "Message": "Rate exceeded"}}
    with patch("lambdas.health_collector.handler.health_client") as mock_health, \
         patch("lambdas.health_collector.handler.dynamodb") as mock_ddb, \
         patch("lambdas.health_collector.handler.s3_client"):
        mock_paginator = MagicMock()
        mock_paginator.paginate.side_effect = ClientError(error_response, "DescribeEventsForOrganization")
        mock_health.get_paginator.return_value = mock_paginator
        mock_table = MagicMock()
        mock_table.get_item.return_value = {}
        mock_ddb.Table.return_value = mock_table

        from lambdas.health_collector import handler as h
        with patch.object(h, "dynamodb", mock_ddb), \
             patch.object(h, "health_client", mock_health):
            with pytest.raises(Exception):
                h.handler({}, None)
