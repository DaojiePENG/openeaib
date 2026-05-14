"""Built-in subagent configurations."""

from .bash_agent import BASH_AGENT_CONFIG
from .eaib import EAIB_SUBAGENTS
from .general_purpose import GENERAL_PURPOSE_CONFIG

__all__ = [
    "GENERAL_PURPOSE_CONFIG",
    "BASH_AGENT_CONFIG",
    "EAIB_SUBAGENTS",
]

# Registry of built-in subagents
BUILTIN_SUBAGENTS = {
    "general-purpose": GENERAL_PURPOSE_CONFIG,
    "bash": BASH_AGENT_CONFIG,
    **EAIB_SUBAGENTS,
}
