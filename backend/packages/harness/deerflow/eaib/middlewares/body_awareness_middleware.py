"""Body Awareness Middleware.

岛叶皮层 (Insular Cortex): injects the current robot body state into agent state
at the start of every turn so all downstream middlewares and the model have
up-to-date hardware context.

Positioned after ThreadDataMiddleware so thread_id is available.
"""

from __future__ import annotations

import logging
from typing import NotRequired, override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langgraph.runtime import Runtime

from deerflow.agents.features import Next
from deerflow.agents.middlewares.thread_data_middleware import ThreadDataMiddleware
from deerflow.eaib.body.body_profile import BodyProfile
from deerflow.eaib.body.body_registry import get_body_registry
from deerflow.eaib.state import BodyState

logger = logging.getLogger(__name__)


class BodyAwarenessState(AgentState):
    """Compatible with EAIBState schema."""

    body_state: NotRequired[BodyState | None]


@Next(ThreadDataMiddleware)
class BodyAwarenessMiddleware(AgentMiddleware[BodyAwarenessState]):
    """Injects the current robot body profile into agent state each turn.

    This ensures:
    - The model's system prompt can reference current body_id and sensors
    - Safety and skill middlewares know which robot is active
    - No tool call is needed just to discover body context
    """

    state_schema = BodyAwarenessState

    @override
    def before_agent(self, state: BodyAwarenessState, runtime: Runtime) -> dict | None:
        try:
            registry = get_body_registry()
            body_id = registry.current_body_id
            profile: BodyProfile | None = registry.get(body_id)

            if profile is None:
                # Gracefully degrade: host-only mode, no hardware configured yet
                return None

            body_state: BodyState = {
                "body_id": body_id,
                "profile_dict": profile.to_dict(),
                "sensors": {s.sensor_type: s.__dict__ for s in profile.sensors},
                "sdk_packages": list(profile.sdk_packages),
                "last_updated": profile.last_updated,
            }
            logger.debug("BodyAwarenessMiddleware: injected body_state for body_id='%s'", body_id)
            return {"body_state": body_state}
        except Exception as exc:
            logger.warning("BodyAwarenessMiddleware: could not load body state: %s", exc)
            return None
