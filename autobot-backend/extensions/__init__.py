# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""
Re-export shim for backwards compatibility (#7426).

The extensions package has been renamed to middleware to clarify that
these are lifecycle hooks (middleware), not loadable plugins.

This shim re-exports all public APIs from middleware/ so existing code
continues to work. Remove this shim after one release cycle.

New code should import from middleware instead:
    from middleware import Extension, HookPoint, get_extension_manager
"""

# Re-export everything for backwards compat
# Note: middleware refactoring incomplete - imports still from extensions
from extensions.base import Extension, HookContext
from extensions.manager import ExtensionManager, get_extension_manager, reset_extension_manager
from extensions.hooks import (
    HOOK_METADATA,
    HookInvocationConfig,
    HookInvoker,
    HookPoint,
    InvocationMode,
    get_hook_metadata,
)

__all__ = [
    # Hook definitions
    "HookPoint",
    "HOOK_METADATA",
    "get_hook_metadata",
    # Base classes
    "Extension",
    "HookContext",
    # Manager
    "ExtensionManager",
    "get_extension_manager",
    "reset_extension_manager",
    # HookInvoker (Issue #4202)
    "HookInvoker",
    "HookInvocationConfig",
    "InvocationMode",
]
