"""create items table"""
import sqlalchemy as sa
from alembic import op

revision = "0001_create_items"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=False, server_default="OTHER"),
        sa.Column("location", sa.String(length=120), nullable=False),
        sa.Column("reported_by", sa.String(length=80), nullable=False),
        sa.Column("contact", sa.String(length=120), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=10), nullable=False, server_default="OPEN"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    # The board is always filtered by type and status, so index them.
    op.create_index("ix_items_type_status", "items", ["type", "status"])


def downgrade():
    op.drop_index("ix_items_type_status", table_name="items")
    op.drop_table("items")
