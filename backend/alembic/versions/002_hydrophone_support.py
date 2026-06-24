"""hydrophone_support

Revision ID: 002_hydrophone_support
Revises: 8f8107ac11cc
Create Date: 2026-06-24

Phase 10.1 — Hydrophone / Bio-Acoustic Intelligence Integration

This migration is additive only.
It does NOT modify or drop any existing columns, tables, constraints, or indices.

Changes applied:
  1. Add 'hydrophone' to the ck_sensor_type_valid CHECK constraint on `sensors`.
  2. Add `acoustic_db` (NUMERIC 6,2) column to `tank_environment_snapshots`.
  3. Add `bio_acoustic_sync` (NUMERIC 5,2) column to `tank_environment_snapshots`.
  4. Add CHECK constraint ck_env_snapshot_bio_acoustic_sync_range (0..100) on `bio_acoustic_sync`.

Rollback (downgrade):
  - Drops newly added columns and the new CHECK constraint.
  - Restores the sensor type CHECK constraint to exclude 'hydrophone'.

IMPORTANT: Do NOT modify 8f8107ac11cc_initial_migration.py.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "002_hydrophone_support"
down_revision: Union[str, None] = "8f8107ac11cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # ── 1. Extend sensor type CHECK constraint to include 'hydrophone' ────────
    # PostgreSQL requires dropping and re-creating CHECK constraints.
    if dialect == "postgresql":
        op.execute("ALTER TABLE sensors DROP CONSTRAINT IF EXISTS ck_sensor_type_valid")
        op.execute(
            "ALTER TABLE sensors ADD CONSTRAINT ck_sensor_type_valid "
            "CHECK (type IN ('temperature','pH','dissolved_oxygen','ammonia',"
            "'salinity','feeder','aerator','hydrophone'))"
        )
    # SQLite does not enforce CHECK constraints added after table creation —
    # the model-level definition is sufficient for non-PostgreSQL environments.

    # ── 2. Add acoustic columns to tank_environment_snapshots ─────────────────
    # Guard: only add columns if they don't already exist (idempotent).
    inspector = sa.inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("tank_environment_snapshots")}

    if "acoustic_db" not in existing_cols:
        op.add_column(
            "tank_environment_snapshots",
            sa.Column(
                "acoustic_db",
                sa.Numeric(precision=6, scale=2),
                nullable=True,
                comment="Current hydrophone acoustic level in decibels",
            ),
        )

    if "bio_acoustic_sync" not in existing_cols:
        op.add_column(
            "tank_environment_snapshots",
            sa.Column(
                "bio_acoustic_sync",
                sa.Numeric(precision=5, scale=2),
                nullable=True,
                comment=(
                    "Confidence score representing correlation between acoustic activity "
                    "and expected biological behavior (0.00 … 100.00)"
                ),
            ),
        )

    # ── 3. Add range CHECK constraint on bio_acoustic_sync (PostgreSQL only) ──
    if dialect == "postgresql":
        # Check if constraint already exists before adding
        op.execute(
            "DO $$ BEGIN "
            "  IF NOT EXISTS ("
            "    SELECT 1 FROM pg_constraint "
            "    WHERE conname = 'ck_env_snapshot_bio_acoustic_sync_range'"
            "  ) THEN "
            "    ALTER TABLE tank_environment_snapshots "
            "    ADD CONSTRAINT ck_env_snapshot_bio_acoustic_sync_range "
            "    CHECK (bio_acoustic_sync BETWEEN 0.00 AND 100.00); "
            "  END IF; "
            "END $$"
        )


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name

    # ── 1. Remove bio_acoustic_sync CHECK constraint ──────────────────────────
    if dialect == "postgresql":
        op.execute(
            "ALTER TABLE tank_environment_snapshots "
            "DROP CONSTRAINT IF EXISTS ck_env_snapshot_bio_acoustic_sync_range"
        )

    # ── 2. Drop acoustic columns ──────────────────────────────────────────────
    inspector = sa.inspect(bind)
    existing_cols = {col["name"] for col in inspector.get_columns("tank_environment_snapshots")}

    if "bio_acoustic_sync" in existing_cols:
        op.drop_column("tank_environment_snapshots", "bio_acoustic_sync")

    if "acoustic_db" in existing_cols:
        op.drop_column("tank_environment_snapshots", "acoustic_db")

    # ── 3. Revert sensor type CHECK constraint to exclude 'hydrophone' ────────
    if dialect == "postgresql":
        op.execute("ALTER TABLE sensors DROP CONSTRAINT IF EXISTS ck_sensor_type_valid")
        op.execute(
            "ALTER TABLE sensors ADD CONSTRAINT ck_sensor_type_valid "
            "CHECK (type IN ('temperature','pH','dissolved_oxygen','ammonia',"
            "'salinity','feeder','aerator'))"
        )
