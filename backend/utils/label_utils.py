"""Label resolution utilities."""

from models.ai_result import AIResult


def get_final_label(record: AIResult) -> str | None:
    """
    Return the effective label for an AI result.

    Prefers the user-corrected label over the AI-predicted one.
    """
    return record.user_label if record.user_label is not None else record.ai_label