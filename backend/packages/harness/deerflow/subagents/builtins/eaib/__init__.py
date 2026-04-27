"""EAIB (Embodied AI Brain) built-in subagent configurations.

Each subagent models a distinct functional region of the brain:
- eaib-sensory   : Sensory cortex — perceives and encodes environmental input
- eaib-motor     : Motor cortex   — plans and executes physical actions
- eaib-memory    : Hippocampus    — manages episodic and semantic memory
- eaib-safety    : Amygdala       — enforces safety constraints and halt signals
- eaib-executive : Prefrontal cortex — high-level planning and module coordination
"""

from .executive import EAIB_EXECUTIVE_CONFIG
from .memory import EAIB_MEMORY_CONFIG
from .motor import EAIB_MOTOR_CONFIG
from .safety import EAIB_SAFETY_CONFIG
from .sensory import EAIB_SENSORY_CONFIG

__all__ = [
    "EAIB_SENSORY_CONFIG",
    "EAIB_MOTOR_CONFIG",
    "EAIB_MEMORY_CONFIG",
    "EAIB_SAFETY_CONFIG",
    "EAIB_EXECUTIVE_CONFIG",
]

# Mapping from subagent name to config — consumed by the parent registry
EAIB_SUBAGENTS: dict = {
    "eaib-sensory": EAIB_SENSORY_CONFIG,
    "eaib-motor": EAIB_MOTOR_CONFIG,
    "eaib-memory": EAIB_MEMORY_CONFIG,
    "eaib-safety": EAIB_SAFETY_CONFIG,
    "eaib-executive": EAIB_EXECUTIVE_CONFIG,
}
