# app/services/user_service.py

from typing import List, Optional
from uuid import UUID

from app.models.user import User, AuditLog
from app.repositories.user_repository import UserRepository
from app.services.base import BaseService


class UserService(BaseService):
    """
    Service managing user profiles, preferences, and security audit trails.
    """

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def get_user_profile(self, user_id: UUID) -> Optional[User]:
        """
        Retrieves a user profile by their ID.
        """
        return await self.user_repo.get(user_id)

    async def get_user_audit_logs(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """
        Retrieves all historical security/operational audit logs associated with a user.
        """
        return await self.user_repo.get_audit_logs(user_id=user_id, skip=skip, limit=limit)
