# app/repositories/audit_log_repository.py

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AuditLog
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    """Repository class for AuditLog operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def create_audit_log(
        self,
        event_type: str,
        action: str,
        ip_address: str,
        user_id: Optional[UUID] = None,
        target_entity: Optional[str] = None,
        target_id: Optional[UUID] = None,
        old_value: Optional[dict] = None,
        new_value: Optional[dict] = None,
    ) -> AuditLog:
        """Create and persist a new audit log record."""
        audit_log = AuditLog(
            time=datetime.now(timezone.utc),
            event_type=event_type,
            user_id=user_id,
            action=action,
            target_entity=target_entity,
            target_id=target_id,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
        )
        self.session.add(audit_log)
        await self.session.flush()
        return audit_log

    async def get_user_audit_logs(
        self, user_id: UUID, skip: int = 0, limit: int = 100
    ) -> List[AuditLog]:
        """Retrieves audit trail events logged for a specific user."""
        query = (
            select(self.model)
            .where(self.model.user_id == user_id)
            .order_by(desc(self.model.time))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
