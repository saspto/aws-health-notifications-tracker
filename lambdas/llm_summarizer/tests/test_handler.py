import json
from unittest.mock import MagicMock, patch
import pytest


def make_stream_record(event_arn: str, account_id: str, llm_processed: bool = False, event_name: str = "INSERT") -> dict:
    return {
        "eventName": event_name,
        "dynamodb": {
            "NewImage": {
                "eventArn": {"S": event_arn},
                "accountId": {"S": account_id},
                "service": {"S": "ECS"},
                "eventTypeCode": {"S": "AWS_ECS_MAINTENANCE_SCHEDULED"},
                "startTime": {"S": "2026-04-01T00:00:00+00:00"},
                "endTime": {"S": "2026-05-01T00:00:00+00:00"},
                "rawDescription": {"S": "ECS maintenance scheduled"},
                "llmProcessed": {"BOOL": llm_processed},
            }
        },
    }


VALID_LLM_RESPONSE = json.dumps({
    "summary": "AWS is scheduling maintenance on ECS clusters in us-east-1.",
    "recommendedActions": ["Review cluster config", "Schedule downtime", "Notify stakeholders"],
    "urgency": "High",
    "deadline": "2026-05-01T00:00:00Z",
})


def mock_bedrock_response(text: str) -> dict:
    body_mock = MagicMock()
    body_mock.read.return_value = json.dumps({
        "content": [{"text": text}]
    }).encode()
    return {"body": body_mock}


def test_bedrock_invocation_correct_prompt():
    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_bedrock.invoke_model.return_value = mock_bedrock_response(VALID_LLM_RESPONSE)
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": [make_stream_record("arn:test", "123456")]}, None)

        mock_bedrock.invoke_model.assert_called_once()
        call_kwargs = mock_bedrock.invoke_model.call_args[1]
        assert call_kwargs["modelId"] == "anthropic.claude-haiku-4-5-20251001"


def test_parse_valid_llm_response():
    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_bedrock.invoke_model.return_value = mock_bedrock_response(VALID_LLM_RESPONSE)
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": [make_stream_record("arn:test", "123456")]}, None)

        mock_table.update_item.assert_called_once()
        update_args = mock_table.update_item.call_args[1]
        assert update_args["ExpressionAttributeValues"][":s"] == "AWS is scheduling maintenance on ECS clusters in us-east-1."
        assert update_args["ExpressionAttributeValues"][":p"] is True


def test_parse_malformed_llm_response_retries():
    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_bedrock.invoke_model.side_effect = [
            mock_bedrock_response("not valid json at all!!!"),
            mock_bedrock_response(VALID_LLM_RESPONSE),
        ]
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": [make_stream_record("arn:test", "123456")]}, None)

        assert mock_bedrock.invoke_model.call_count == 2


def test_urgency_classification_critical():
    from datetime import datetime, timezone, timedelta
    deadline = (datetime.now(timezone.utc) + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    response_text = json.dumps({
        "summary": "Critical maintenance.",
        "recommendedActions": ["Act now"],
        "urgency": "Critical",
        "deadline": deadline,
    })

    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_bedrock.invoke_model.return_value = mock_bedrock_response(response_text)
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": [make_stream_record("arn:test", "123456")]}, None)

        update_args = mock_table.update_item.call_args[1]
        assert update_args["ExpressionAttributeValues"][":u"] == "Critical"


def test_urgency_classification_low():
    response_text = json.dumps({
        "summary": "Low priority.",
        "recommendedActions": ["Monitor"],
        "urgency": "Low",
        "deadline": None,
    })

    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_bedrock.invoke_model.return_value = mock_bedrock_response(response_text)
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": [make_stream_record("arn:test", "123456")]}, None)

        update_args = mock_table.update_item.call_args[1]
        assert update_args["ExpressionAttributeValues"][":u"] == "Low"


def test_skips_already_processed_events():
    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": [make_stream_record("arn:test", "123456", llm_processed=True)]}, None)

        mock_bedrock.invoke_model.assert_not_called()


def test_batch_processes_multiple_records():
    with patch("lambdas.llm_summarizer.handler.bedrock_client") as mock_bedrock, \
         patch("lambdas.llm_summarizer.handler.dynamodb") as mock_ddb:
        mock_bedrock.invoke_model.return_value = mock_bedrock_response(VALID_LLM_RESPONSE)
        mock_table = MagicMock()
        mock_ddb.Table.return_value = mock_table

        records = [make_stream_record(f"arn:test:{i}", f"account{i}") for i in range(5)]

        from lambdas.llm_summarizer import handler as h
        with patch.object(h, "bedrock_client", mock_bedrock), \
             patch.object(h, "dynamodb", mock_ddb):
            h.handler({"Records": records}, None)

        assert mock_bedrock.invoke_model.call_count == 5
