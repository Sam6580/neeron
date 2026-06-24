from typing import Any, Generic, List, Optional, Type, TypeVar
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, update

from app.db.base import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Generic Base Repository containing common CRUD operations.
    Fully asynchronous and typed.
    """

    def __init__(self, model: Type[T], session: AsyncSession):
        self.model = model
        self.session = session

    async def get(self, id: Any) -> Optional[T]:
        """
        Fetch a single record by its primary key.
        Supports composite keys passed as a tuple/list (e.g. (id, time)).
        """
        # For soft-deleted models, verify it hasn't been soft deleted
        if hasattr(self.model, "deleted_at"):
            # If composite PK, id will be a tuple/list
            db_obj = await self.session.get(self.model, id)
            if db_obj and getattr(db_obj, "deleted_at") is not None:
                return None
            return db_obj
        return await self.session.get(self.model, id)

    async def get_by_id(self, id: Any) -> Optional[T]:
        """Alias helper for get()."""
        return await self.get(id)

    async def exists(self, id: Any) -> bool:
        """Check if a record exists by its primary key."""
        obj = await self.get(id)
        return obj is not None

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100, filters: Optional[dict] = None
    ) -> List[T]:
        """
        Retrieve multiple records with pagination and filtering.
        Soft-deleted records are automatically filtered out.
        """
        query = select(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        if filters:
            query = query.filter_by(**filters)
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: Any) -> T:
        """Create a new database record from a model instance or dict."""
        if isinstance(obj_in, dict):
            db_obj = self.model(**obj_in)
        else:
            db_obj = obj_in
        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def update(self, db_obj: T, obj_in: Any) -> T:
        """Update an existing database record."""
        obj_data = db_obj.__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.__dict__

        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])

        self.session.add(db_obj)
        await self.session.flush()
        return db_obj

    async def delete(self, id: Any) -> Optional[T]:
        """
        Deletes a record by primary key.
        Performs a soft delete if the model has a `deleted_at` field,
        otherwise performs a hard physical delete.
        """
        db_obj = await self.get(id)
        if not db_obj:
            return None

        if hasattr(db_obj, "deleted_at"):
            from datetime import datetime, timezone
            setattr(db_obj, "deleted_at", datetime.now(timezone.utc))
            self.session.add(db_obj)
        else:
            await self.session.delete(db_obj)

        await self.session.flush()
        return db_obj

    async def bulk_create(self, list_obj_in: List[Any]) -> List[T]:
        """Bulk insert multiple records into the database."""
        db_objs = []
        for obj_in in list_obj_in:
            if isinstance(obj_in, dict):
                db_obj = self.model(**obj_in)
            else:
                db_obj = obj_in
            db_objs.append(db_obj)
        self.session.add_all(db_objs)
        await self.session.flush()
        return db_objs

    async def count(self, filters: Optional[dict] = None) -> int:
        """Count the number of active records matching the filters."""
        query = select(func.count()).select_from(self.model)
        if hasattr(self.model, "deleted_at"):
            query = query.where(self.model.deleted_at.is_(None))
        if filters:
            query = query.filter_by(**filters)
        result = await self.session.execute(query)
        return result.scalar() or 0
