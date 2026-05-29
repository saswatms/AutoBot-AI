# AutoBot - AI-Powered Automation Platform
# Copyright (c) 2025 mrveiss
# Author: mrveiss
"""User endpoints for per-user voice bundle assignment (GH#8605).

Endpoints:
    GET  /api/voice/bundles                    — list available bundles
    GET  /api/voice/users/{userId}/bundle     — get user's bundle (self/admin only)
    PUT  /api/voice/users/{userId}/bundle     — assign/clear bundle (self/admin only)
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from auth_middleware import get_current_user
from autobot_shared.logging_manager import get_logger
from services.audit.unified_audit import EventType, emit  # GH#8290 Phase 2
from utils.catalog_http_exceptions import raise_auth_error

logger = get_logger(__name__)

router = APIRouter(tags=["voice", "rbac"])

# Valid voice bundles
VALID_BUNDLES = {"voice_safe", "voice_extended", "voice_admin"}

# Bundle definitions with labels
BUNDLE_DEFINITIONS = {
    "voice_safe": {
        "label": "Safe",
        "description": "Basic voice commands for standard users",
    },
    "voice_extended": {
        "label": "Extended",
        "description": "Extended voice commands with advanced features",
    },
    "voice_admin": {
        "label": "Admin",
        "description": "Full voice command set for administrators",
    },
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class BundleInfo(BaseModel):
    """Information about an available voice bundle."""

    name: str
    label: str
    tool_count: int


class UserBundleResponse(BaseModel):
    """User's voice bundle assignment."""

    user_id: str
    bundle_name: Optional[str] = None


class BundleAssignRequest(BaseModel):
    """Request to assign or clear a bundle for a user."""

    bundle_name: Optional[str] = None  # None = clear override


# ---------------------------------------------------------------------------
# GET /bundles
# ---------------------------------------------------------------------------


async def _count_tools_for_bundle(bundle: str, is_admin: bool) -> int:
    """Return the number of tools available in this bundle."""
    from api.redis_mcp.rbac import TOOL_ACCESS_MATRIX, filter_tools_for_bundle  # noqa: PLC0415

    all_tools = list(TOOL_ACCESS_MATRIX.keys())
    return len(filter_tools_for_bundle(all_tools, bundle=bundle, is_admin=is_admin))


@router.get("/bundles", response_model=list[BundleInfo])
async def list_bundles(
    current_user: dict = Depends(get_current_user),
) -> list[BundleInfo]:
    """List all available voice bundles with tool counts."""
    is_admin = current_user.get("role") == "admin"

    bundles = []
    for bundle_name in sorted(VALID_BUNDLES):
        bundle_def = BUNDLE_DEFINITIONS.get(bundle_name, {})
        tool_count = await _count_tools_for_bundle(bundle_name, is_admin=is_admin)

        bundles.append(
            BundleInfo(
                name=bundle_name,
                label=bundle_def.get("label", bundle_name),
                tool_count=tool_count,
            )
        )

    return bundles


# ---------------------------------------------------------------------------
# GET /users/{userId}/bundle
# ---------------------------------------------------------------------------


@router.get("/users/{user_id}/bundle", response_model=UserBundleResponse)
async def get_user_bundle(
    user_id: str,
    current_user: dict = Depends(get_current_user),
) -> UserBundleResponse:
    """Get a user's voice bundle assignment.

    Permission: Self or admin only.
    """
    # Check permissions: only self or admin
    caller_id = current_user.get("user_id") or current_user.get("sub") or current_user.get("username")
    is_admin = current_user.get("role") == "admin"

    if str(caller_id) != str(user_id) and not is_admin:
        raise_auth_error("AUTH_0003", "Permission denied")

    try:
        from database.session import get_async_session  # noqa: PLC0415
        from sqlalchemy import text  # noqa: PLC0415

        async with get_async_session() as db_session:
            row = await db_session.execute(
                text("SELECT bundle_name FROM user_voice_bundle WHERE user_id = :uid"),
                {"uid": user_id},
            )
            result = row.fetchone()
            bundle_name = result[0] if result else None
    except Exception as exc:
        logger.error("get_user_bundle: DB error: %s", exc)
        raise HTTPException(status_code=500, detail="Database error") from exc

    return UserBundleResponse(user_id=user_id, bundle_name=bundle_name)


# ---------------------------------------------------------------------------
# PUT /users/{userId}/bundle
# ---------------------------------------------------------------------------


@router.put("/users/{user_id}/bundle", response_model=UserBundleResponse)
async def set_user_bundle(
    user_id: str,
    body: BundleAssignRequest,
    current_user: dict = Depends(get_current_user),
) -> UserBundleResponse:
    """Assign or clear a voice bundle override for a user.

    Permission: Self or admin only. Non-admin users cannot assign voice_admin bundle.
    """
    # Check permissions: only self or admin
    caller_id = current_user.get("user_id") or current_user.get("sub") or current_user.get("username")
    is_admin = current_user.get("role") == "admin"

    if str(caller_id) != str(user_id) and not is_admin:
        raise_auth_error("AUTH_0003", "Permission denied")

    # Validate bundle name
    if body.bundle_name is not None and body.bundle_name not in VALID_BUNDLES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid bundle_name '{body.bundle_name}'. Valid: {sorted(VALID_BUNDLES)}",
        )

    # Non-admin users cannot assign voice_admin bundle
    if body.bundle_name == "voice_admin" and not is_admin:
        raise HTTPException(
            status_code=403,
            detail="Permission denied: Only admins can assign voice_admin bundle",
        )

    try:
        from database.session import get_async_session  # noqa: PLC0415
        from sqlalchemy import text  # noqa: PLC0415

        async with get_async_session() as db_session:
            if body.bundle_name is None:
                # Clear override
                await db_session.execute(
                    text("DELETE FROM user_voice_bundle WHERE user_id = :uid"),
                    {"uid": user_id},
                )
            else:
                # Upsert
                await db_session.execute(
                    text("""
                        INSERT INTO user_voice_bundle (user_id, bundle_name, assigned_by, assigned_at)
                        VALUES (:uid, :bundle, :by, NOW())
                        ON CONFLICT (user_id) DO UPDATE
                          SET bundle_name = EXCLUDED.bundle_name,
                              assigned_by = EXCLUDED.assigned_by,
                              assigned_at = EXCLUDED.assigned_at
                        """),
                    {"uid": user_id, "bundle": body.bundle_name, "by": str(caller_id)},
                )
            await db_session.commit()
    except Exception as exc:
        logger.error("set_user_bundle: DB error: %s", exc)
        raise HTTPException(status_code=500, detail="Database error") from exc

    # Audit log
    emit(
        EventType.CONFIG_CHANGED,
        user_id=str(caller_id),
        resource_type="user_voice_bundle",
        resource_id=user_id,
        metadata={
            "target_user_id": user_id,
            "bundle_name": body.bundle_name,
            "action": "clear" if body.bundle_name is None else "assign",
        },
    )

    logger.info(
        "set_user_bundle caller=%s target=%s bundle=%s",
        caller_id,
        user_id,
        body.bundle_name,
    )

    return UserBundleResponse(user_id=user_id, bundle_name=body.bundle_name)
