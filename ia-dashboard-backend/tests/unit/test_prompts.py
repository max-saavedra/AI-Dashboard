"""
tests/unit/test_prompts.py

Unit tests for app/services/ai/prompts.py.
Verifies that prompts contain the expected sections, context, and constraints
without calling any AI provider.
"""

import json

import pytest

from app.services.ai.prompts import (
    build_chat_qa_prompt,
    build_executive_summary_prompt,
    build_schema_detection_prompt,
)


class TestSchemaDetectionPrompt:
    def test_contains_dataset_profile(self):
        profile = {"row_count": 100, "columns": [{"name": "sales", "inferred_type": "numeric"}]}
        prompt = build_schema_detection_prompt(profile)
        assert "sales" in prompt
        assert "numeric" in prompt

    def test_requests_json_output(self):
        prompt = build_schema_detection_prompt({"columns": []})
        assert "JSON" in prompt

    def test_specifies_minimum_chart_count(self):
        prompt = build_schema_detection_prompt({"columns": []})
        assert "3" in prompt or "three" in prompt.lower()

    def test_instructs_no_markdown(self):
        prompt = build_schema_detection_prompt({"columns": []})
        assert "no markdown" in prompt.lower() or "no explanation" in prompt.lower()


class TestExecutiveSummaryPrompt:
    def test_includes_user_objective_when_provided(self):
        prompt = build_executive_summary_prompt(
            kpi_payload={"kpis": {}},
            schema_summary="Sales data",
            user_objective="Increase Q4 revenue",
        )
        assert "Increase Q4 revenue" in prompt

    def test_omits_objective_block_when_not_provided(self):
        prompt = build_executive_summary_prompt(
            kpi_payload={"kpis": {}},
            schema_summary="Sales data",
        )
        assert "USER OBJECTIVE" not in prompt

    def test_includes_user_tags_when_provided(self):
        prompt = build_executive_summary_prompt(
            kpi_payload={"kpis": {}},
            schema_summary="Sales data",
            tags=["revenue", "growth"],
        )
        assert "revenue" in prompt
        assert "growth" in prompt

    def test_uses_custom_structure_when_provided(self):
        custom = "1. Overview\n2. Next Steps"
        prompt = build_executive_summary_prompt(
            kpi_payload={"kpis": {}},
            schema_summary="Sales data",
            user_structure=custom,
        )
        assert "Next Steps" in prompt
        # Default structure headings should not appear
        assert "Trends & Patterns" not in prompt

    def test_uses_default_structure_when_none_given(self):
        prompt = build_executive_summary_prompt(
            kpi_payload={"kpis": {}},
            schema_summary="Sales data",
        )
        assert "Trends & Patterns" in prompt
        assert "Recommendations" in prompt

    def test_kpi_data_embedded_in_prompt(self):
        kpi_payload = {"kpis": {"revenue": {"sum": 9999}}}
        prompt = build_executive_summary_prompt(
            kpi_payload=kpi_payload,
            schema_summary="Revenue dataset",
        )
        assert "9999" in prompt

    def test_instructs_no_external_knowledge(self):
        prompt = build_executive_summary_prompt(
            kpi_payload={},
            schema_summary="Test",
        )
        assert "exclusively" in prompt.lower() or "only" in prompt.lower()


class TestChatQAPrompt:
    def test_includes_question(self):
        prompt = build_chat_qa_prompt(
            question="What is the total revenue?",
            kpi_payload={"kpis": {"revenue": {"sum": 5000}}},
            schema_summary="Revenue dataset",
        )
        assert "What is the total revenue?" in prompt

    def test_includes_kpi_data(self):
        prompt = build_chat_qa_prompt(
            question="What is the average?",
            kpi_payload={"kpis": {"sales": {"mean": 250.0}}},
            schema_summary="Sales dataset",
        )
        assert "250.0" in prompt

    def test_includes_conversation_history(self):
        history = [
            {"role": "user", "content": "What is the max?"},
            {"role": "assistant", "content": "The max is 1000."},
        ]
        prompt = build_chat_qa_prompt(
            question="And the min?",
            kpi_payload={},
            schema_summary="Dataset",
            conversation_history=history,
        )
        assert "The max is 1000." in prompt

    def test_limits_history_to_last_six_entries(self):
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg {i}"}
            for i in range(20)
        ]
        prompt = build_chat_qa_prompt(
            question="Latest question",
            kpi_payload={},
            schema_summary="Dataset",
            conversation_history=history,
        )
        # Only the last 6 messages should appear; msg 0 should not
        assert "msg 0" not in prompt

    def test_prohibits_external_inference(self):
        prompt = build_chat_qa_prompt(
            question="Any question",
            kpi_payload={},
            schema_summary="Dataset",
        )
        assert "ONLY" in prompt or "only" in prompt
