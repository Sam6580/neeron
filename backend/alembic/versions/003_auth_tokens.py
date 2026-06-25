"""auth_tokens

Revision ID: 003_auth_tokens
Revises: 002_hydrophone_support
Create Date: 2026-06-25

Phase 11.1 — Authentication Hardening & Refresh Token Persistence

This migration adds columns for refresh token persistence:
- refresh_token (VARCHAR(255), nullable)
- refresh_token_expires_at (TIMESTAMP WITH TIME ZONE, nullable)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "003_auth_tokens"
down_revision: Union[str, None] = "002_hydrophone_support"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("users")}

    if "refresh_token" not in existing_cols:
        op.add_column(
            "users",
            sa.Column(
                "refresh_token",
                sa.String(length=255),
                nullable=True,
                comment="Persisted refresh token for authentication hardening",
            ),
        )

    if "refresh_token_expires_at" not in existing_cols:
        op.add_column(
            "users",
            sa.Column(
                "refresh_token_expires_at",
                sa.DateTime(timezone=True),
                nullable=True,
                comment="Expiration timestamp of the stored refresh token",
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("users")}

    if "refresh_token_expires_at" in existing_cols:
        op.drop_column("users", "refresh_token_expires_at")

    if "refresh_token" in existing_cols:
        op.drop_column("users", "refresh_token")
