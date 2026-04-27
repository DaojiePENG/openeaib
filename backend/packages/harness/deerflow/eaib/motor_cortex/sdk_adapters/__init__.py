"""SDK adapters sub-package.

The registry starts EMPTY. Adapters are created through user conversation and
persisted to ~/.local/share/eaib/adapters/<body_id>/adapter.py by the motor
cortex agent. See DynamicSdkAdapter and AdapterRegistry for the workflow.

Reference examples for specific robots are in sdk_adapters/examples/ and are
NOT loaded automatically.
"""

from deerflow.eaib.motor_cortex.sdk_adapters.adapter_registry import (
    AdapterRegistry,
    get_adapter_registry,
    reset_adapter_registry,
)
from deerflow.eaib.motor_cortex.sdk_adapters.base_adapter import BaseSdkAdapter, ConnectionStatus
from deerflow.eaib.motor_cortex.sdk_adapters.dynamic_adapter import DynamicSdkAdapter


def get_adapter(body_id: str) -> BaseSdkAdapter | None:
    """Return the registered adapter for body_id, or None if not yet configured."""
    return get_adapter_registry().get(body_id)


__all__ = [
    "BaseSdkAdapter",
    "ConnectionStatus",
    "DynamicSdkAdapter",
    "AdapterRegistry",
    "get_adapter_registry",
    "reset_adapter_registry",
    "get_adapter",
]
