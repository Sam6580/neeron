"""performance_indexes

Revision ID: 004_performance_indexes
Revises: 003_auth_tokens
Create Date: 2026-06-25
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_performance_indexes"
down_revision: Union[str, None] = "003_auth_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_recommendations_generated_by_model",
        "recommendations",
        ["generated_by_model"],
    )
    op.create_index(
        "ix_recommendations_resolved_by",
        "recommendations",
        ["resolved_by"],
    )
    op.create_index(
        "ix_alerts_resolved_by",
        "alerts",
        ["resolved_by"],
    )
    op.create_index(
        "ix_ai_insights_source_model_id",
        "ai_insights",
        ["source_model_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_ai_insights_source_model_id", table_name="ai_insights")
    op.drop_index("ix_alerts_resolved_by", table_name="alerts")
    op.drop_index("ix_recommendations_resolved_by", table_name="recommendations")
    op.drop_index("ix_recommendations_generated_by_model", table_name="recommendations")
