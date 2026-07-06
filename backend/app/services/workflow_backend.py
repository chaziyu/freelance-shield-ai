import os

from app.services.errors import ConfigurationError

LOCAL_WORKFLOW_ENV = "FREELANCE_SHIELD_ALLOW_LOCAL_WORKFLOW"


def require_configured_workflow_backend() -> None:
    if os.getenv(LOCAL_WORKFLOW_ENV) == "1":
        return

    if os.getenv("GOOGLE_API_KEY"):
        return

    raise ConfigurationError(
        "Google ADK model configuration is required for workflow writes. "
        f"Set GOOGLE_API_KEY, or use {LOCAL_WORKFLOW_ENV}=1 only for local tests."
    )


def use_local_workflow() -> bool:
    return os.getenv(LOCAL_WORKFLOW_ENV) == "1"
