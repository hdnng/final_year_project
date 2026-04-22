def get_final_label(record):
    return record.user_label if record.user_label is not None else record.ai_label