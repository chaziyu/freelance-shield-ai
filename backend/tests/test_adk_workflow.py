import asyncio
import json
import os
from collections.abc import AsyncGenerator

from google.adk.models import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from app.db.sqlite import initialize_database
from app.repositories.workflow import WorkflowRepository
from app.schemas.workflow import IntakeAnalyseRequest
from app.services.adk_workflow import AdkWorkflowService

initialize_database()

# Ensure environment vars are populated for local testing
os.environ["FREELANCE_SHIELD_ALLOW_LOCAL_WORKFLOW"] = "1"
os.environ["REVIEW_TERMS_ATTESTATION_HMAC_KEY"] = (
    "test-attestation-secret-key-1234567890-at-least-32-chars"
)
os.environ["SAFETY_RECEIPT_HMAC_KEY"] = (
    "test-safety-receipt-secret-key-1234567890-at-least-32"
)


class IntakeModelFake(BaseLlm):
    async def generate_content_async(
        self, request, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        sys_inst = ""
        if request.config and request.config.system_instruction:
            if isinstance(request.config.system_instruction, str):
                sys_inst = request.config.system_instruction
            elif hasattr(request.config.system_instruction, "parts"):
                sys_inst = "".join(
                    p.text for p in request.config.system_instruction.parts if p.text
                )

        if "CoordinatorAgent" in sys_inst:
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=json.dumps(
                                {
                                    "intent": "analyze_discussion",
                                    "safe_summary": "Routed",
                                }
                            )
                        )
                    ],
                )
            )
            return

        if "DiscussionAgent" in sys_inst:
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=json.dumps(
                                {
                                    "title": "Synthetic Poster Project",
                                    "scope": {
                                        "value": "Design a promotional poster.",
                                        "evidence_quote": "Need a poster",
                                        "confidence": 0.95,
                                    },
                                    "deliverables": {
                                        "value": ["One final poster file."],
                                        "evidence_quote": "Need a poster",
                                        "confidence": 0.9,
                                    },
                                    "fee_amount_minor": {
                                        "value": 80000,
                                        "evidence_quote": "RM800",
                                        "confidence": 0.99,
                                    },
                                    "currency": {
                                        "value": "MYR",
                                        "evidence_quote": "RM800",
                                        "confidence": 0.99,
                                    },
                                    "deadline": {
                                        "value": "2026-07-10",
                                        "evidence_quote": "Friday",
                                        "confidence": 0.8,
                                    },
                                    "revision_limit": {
                                        "value": 2,
                                        "evidence_quote": "Two revisions",
                                        "confidence": 0.95,
                                    },
                                    "payment_terms": {
                                        "value": "Payment due after invoice.",
                                        "evidence_quote": "invoice",
                                        "confidence": 0.5,
                                    },
                                    "missing_fields": [],
                                    "risk_flags": [],
                                }
                            )
                        )
                    ],
                )
            )
            return

        if "SafetyAuditAgent" in sys_inst:
            yield LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text=json.dumps(
                                {
                                    "decision": "safe_to_show",
                                    "blocked": False,
                                    "warnings": [],
                                    "blocked_reasons": [],
                                    "required_human_review": False,
                                }
                            )
                        )
                    ],
                )
            )
            return

        yield LlmResponse(
            content=types.Content(role="model", parts=[types.Part(text="fallback")])
        )


def test_adk_coordinator_runs_intake_agent_through_stdio_mcp() -> None:
    result = asyncio.run(
        AdkWorkflowService(IntakeModelFake(model="fake")).analyse_intake(
            IntakeAnalyseRequest(
                chat_text=(
                    "Need a poster by Friday. RM800. Two revisions. Payment due after invoice."  # noqa: E501
                ),
                source_platform="Instagram",
            )
        )
    )

    assert result.extracted_facts.amount == 800
    assert {row.actor for row in result.trace} >= {
        "CoordinatorAgent",
        "DiscussionAgent",
    }
    assert {row.action for row in result.trace} >= {
        "message_generated",
    }
    audits = WorkflowRepository().list_audit(result.project.id)
    assert len(audits) > 0
    assert any(event.action == "project_created" for event in audits)
