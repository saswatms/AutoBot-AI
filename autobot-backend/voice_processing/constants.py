# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""
Voice Processing Constants

MIGRATION (Issue #GH7440):
    Some constants were moved from ssot_constants. This module provides backward compatibility.
    Import directly from autobot_shared.ssot_constants for shared constants.
"""
import re

# Re-export from ssot_constants (these exist there)
from autobot_shared.ssot_constants import (  # noqa: F401
    AUTOMATION_INTENT_PATTERNS,
    HIGH_RISK_INTENTS,
    NUMBER_RE,
    QUOTED_TEXT_RE,
    URL_RE,
)

# Local voice-processing-specific constants (not in ssot_constants)
APP_PATTERNS_RE = [
    re.compile(r"\b(chrome|firefox|safari|edge)\b", re.IGNORECASE),
    re.compile(r"\b(vscode|code|editor)\b", re.IGNORECASE),
    re.compile(r"\b(terminal|console|shell)\b", re.IGNORECASE),
]

DIRECTION_RE = re.compile(r"\b(up|down|left|right|top|bottom)\b", re.IGNORECASE)

NAVIGATION_INTENT_PATTERNS = [
    (re.compile(r"go to (.+)", re.IGNORECASE), "navigate"),
    (re.compile(r"navigate to (.+)", re.IGNORECASE), "navigate"),
    (re.compile(r"open (.+)", re.IGNORECASE), "navigate"),
]

QUERY_INTENT_PATTERNS = [
    (re.compile(r"what is (.+)", re.IGNORECASE), "information_query"),
    (re.compile(r"show me (.+)", re.IGNORECASE), "information_query"),
    (re.compile(r"find (.+)", re.IGNORECASE), "information_query"),
]

CONTEXT_DEPENDENT_INTENTS = {"click", "type", "scroll", "navigate"}

SCREEN_STATE_INTENTS = {"show", "hide", "toggle"}

HIGH_RISK_COMMAND_TYPES = {"delete", "remove", "shutdown", "restart", "format", "modify_system"}


def match_intent_from_patterns(text: str, patterns: list, intent_type: str) -> dict | None:
    """Match text against intent patterns and return extracted intent."""
    for pattern, intent in patterns:
        match = pattern.search(text)
        if match:
            return {"type": intent_type, "intent": intent, "entities": match.groups()}
    return None
