"""add resolved_at to items

Nullable on purpose: existing rows have no value, so adding the column needs no
default and no table rewrite - it is safe to run against a live table.
"""
import sqlalchemy as sa
from alembic import op

revision = "0002_add_resolved_at"
down_revision = "0001_create_items"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("items", sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))


def downgrade():
    op.drop_column("items", "resolved_at")
