from datetime import date

from app.schemas.workflow import DraftType, FollowUpPolicy, Project, ProjectStatus


def evaluate_follow_up_policy(project: Project, current_date: date) -> FollowUpPolicy:
    if project.dispute_flag or project.status == ProjectStatus.DISPUTED:
        return FollowUpPolicy(
            allowed_draft_type=DraftType.DISPUTE_CLARIFICATION,
            reason_codes=["PROJECT_DISPUTED"],
            blocked_draft_types=[DraftType.PAYMENT_REMINDER],
        )

    if project.status not in {
        ProjectStatus.ACCEPTED,
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.DELIVERED,
        ProjectStatus.INVOICED,
        ProjectStatus.OVERDUE,
    }:
        return FollowUpPolicy(
            allowed_draft_type=DraftType.ACCEPTANCE_REQUEST,
            reason_codes=["NO_ACCEPTED_AGREEMENT"],
            blocked_draft_types=[DraftType.PAYMENT_REMINDER],
        )

    if project.invoice_due_date and project.invoice_due_date < current_date:
        return FollowUpPolicy(
            allowed_draft_type=DraftType.PAYMENT_REMINDER,
            reason_codes=["INVOICE_OVERDUE"],
            blocked_draft_types=[],
        )

    return FollowUpPolicy(
        allowed_draft_type=DraftType.DELIVERY_CONFIRMATION,
        reason_codes=["NO_OVERDUE_INVOICE"],
        blocked_draft_types=[DraftType.PAYMENT_REMINDER],
    )
