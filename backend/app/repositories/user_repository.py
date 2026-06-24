from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, AuditLog
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository class for User operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a user by their unique login email address."""
        query = select(self.model).where(self.model.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_audit_logs(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[AuditLog]:
        """Retrieves audit trail events logged for a specific user."""
        query = (
            select(AuditLog)
            .where(AuditLog.user_id == user_id)
            .order_by(desc(AuditLog.time))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
