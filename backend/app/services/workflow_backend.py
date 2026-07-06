import os

from app.services.errors import ConfigurationError

LOCAL_WORKFLOW_ENV = "FREELANCE_SHIELD_ALLOW_LOCAL_WORKFLOW"


def require_configured_workflow_backend() -> None:
    if os.getenv(LOCAL_WORKFLOW_ENV) == "1":
        return

    raise ConfigurationError(
        "REST-to-ADK coordinator execution is required for production workflow writes. "
        f"Set {LOCAL_WORKFLOW_ENV}=1 only for local scaffold tests."
    )
