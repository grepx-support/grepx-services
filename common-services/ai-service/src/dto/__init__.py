# Copyright (c) 2026 GrepX Private Limited (grepx.sg). All rights reserved.
# This file is part of the GrepX platform and is proprietary and confidential.
# Unauthorised copying, use, modification or distribution is strictly prohibited.

"""Names ai-service publishes."""
from enum import Enum

AI_USAGE = "ai_usage"
AI_JOBS = "ai_jobs"
AI_CHATS = "ai_chats"


class AiAction(str, Enum):
    ASK = "ASK"                  # one question (feature, instructions, question, data, model) -> a job, answered in the background
    CHAT = "CHAT"                # a message in a person's chat (new chat when no chat_id) -> the chat, the answer to come
    CHAT_DELETE = "CHAT_DELETE"  # a person removes one of their chats
    USAGE = "USAGE"              # this month's answers and the limit


class JobState(str, Enum):
    THINKING = "thinking"
    DONE = "done"
    FAILED = "failed"


class ReasonCode(str, Enum):
    MISSING_TENANT = "MISSING_TENANT"
    NO_QUESTION = "NO_QUESTION"
    AI_OFF = "AI_OFF"                  # the business has not switched AI on
    NO_KEY = "NO_KEY"                  # no AI engine reachable (no local engine, no key)
    LIMIT_REACHED = "LIMIT_REACHED"    # this month's answers are used up
    MODEL_FAILED = "MODEL_FAILED"      # the model did not answer (network, overload, timeout)
    UNKNOWN_CHAT = "UNKNOWN_CHAT"
    BUSY = "BUSY"                      # this person already waits for an answer in this chat


__all__ = ["AI_CHATS", "AI_JOBS", "AI_USAGE", "AiAction", "JobState", "ReasonCode"]
