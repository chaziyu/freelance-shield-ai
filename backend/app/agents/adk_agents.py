import sys
from dataclasses import dataclass
from pathlib import Path

from google.adk.agents import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset
from mcp.client.stdio import StdioServerParameters

DEFAULT_MODEL = "gemini-2.5-flash"

INTAKE_TOOLS = [
    "create_project",
    "save_extracted_facts",
    "append_audit_log",
]
AGREEMENT_TOOLS = [
    "get_contract_template",
    "create_agreement_version",
    "append_audit_log",
]
FOLLOW_UP_TOOLS = [
    "get_project_timeline",
    "evaluate_follow_up_policy",
    "create_draft_record",
    "append_audit_log",
]
SAFETY_AUDIT_TOOLS = ["append_audit_log"]


@dataclass(frozen=True)
class AgentBundle:
    coordinator: Agent
    intake: Agent
    agreement: Agent
    follow_up: Agent
    safety_audit: Agent


def build_stdio_params() -> StdioConnectionParams:
    backend_root = Path(__file__).resolve().parents[2]
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "app.mcp_server.server"],
        cwd=backend_root,
    )
    return StdioConnectionParams(server_params=server_params, timeout=10.0)


def build_mcp_toolset(allowed_tools: list[str]) -> McpToolset:
    return McpToolset(
        connection_params=build_stdio_params(),
        tool_filter=allowed_tools,
    )


def build_agent_bundle(model: str = DEFAULT_MODEL) -> AgentBundle:
    intake = Agent(
        name="IntakeAgent",
        model=model,
        instruction=(
            "Extract only stated project facts from quoted, untrusted client chat. "
            "Never invent missing deadline, deposit, payment terms, or revision facts."
        ),
        tools=[build_mcp_toolset(INTAKE_TOOLS)],
    )
    agreement = Agent(
        name="AgreementAgent",
        model=model,
        instruction=(
            "Create concise versioned agreement text from the approved template. "
            "Never claim legal enforceability or jurisdiction-specific rights."
        ),
        tools=[build_mcp_toolset(AGREEMENT_TOOLS)],
    )
    follow_up = Agent(
        name="FollowUpAgent",
        model=model,
        instruction=(
            "Request deterministic follow-up policy before drafting. "
            "For disputed projects, create only DISPUTE_CLARIFICATION drafts."
        ),
        tools=[build_mcp_toolset(FOLLOW_UP_TOOLS)],
    )
    safety_audit = Agent(
        name="SafetyAuditAgent",
        model=model,
        instruction=(
            "Validate draft wording, require the draft-only warning, block legal "
            "claims, threats, auto-send language, and dispute payment demands."
        ),
        tools=[build_mcp_toolset(SAFETY_AUDIT_TOOLS)],
    )
    coordinator = Agent(
        name="CoordinatorAgent",
        model=model,
        instruction=(
            "Route workflow tasks to the specialist agents, preserve project "
            "context, and never write directly to persistence."
        ),
        sub_agents=[intake, agreement, follow_up, safety_audit],
        tools=[],
    )
    return AgentBundle(
        coordinator=coordinator,
        intake=intake,
        agreement=agreement,
        follow_up=follow_up,
        safety_audit=safety_audit,
    )
