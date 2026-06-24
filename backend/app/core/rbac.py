# app/core/rbac.py

from typing import List
from fastapi import Depends, HTTPException, status
from app.models.user import User
from app.api.v1.dependencies.auth import get_current_active_user


class RoleChecker:
    """Dependency checker to restrict endpoints to specific role names."""

    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        role_name = current_user.role.name if current_user.role else None
        if not role_name or role_name not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted. Required roles: {self.allowed_roles}",
            )
        return current_user


class PermissionChecker:
    """Dependency checker to restrict endpoints to specific role permissions.
    
    If the user has the 'Administrator' role, they bypass all permission checks.
    """

    def __init__(self, required_permissions: List[str]):
        self.required_permissions = required_permissions

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        role = current_user.role
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted. No role assigned.",
            )

        # Administrative bypass
        if role.name == "Administrator":
            return current_user

        role_permissions = role.permissions or {}
        for perm in self.required_permissions:
            if not role_permissions.get(perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Operation not permitted. Missing permission: '{perm}'",
                )
        return current_user


def require_roles(*roles: str):
    """FastAPI dependency to require specific roles."""
    return RoleChecker(list(roles))


def require_permissions(*permissions: str):
    """FastAPI dependency to require specific permissions."""
    return PermissionChecker(list(permissions))
