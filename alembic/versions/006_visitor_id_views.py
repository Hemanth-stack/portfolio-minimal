"""Replace ip_address with visitor_id in post_views for cookie-based tracking

Revision ID: 006_visitor_id_views
Revises: 005_add_indexing_logs
Create Date: 2026-03-07

"""
from alembic import op
import sqlalchemy as sa

revision = '006_visitor_id_views'
down_revision = '005_add_indexing_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add visitor_id column (nullable first for existing rows)
    op.add_column('post_views', sa.Column('visitor_id', sa.String(36), nullable=True))

    # Backfill existing rows: copy ip_address into visitor_id so no data is lost
    op.execute("UPDATE post_views SET visitor_id = ip_address WHERE visitor_id IS NULL")

    # Make visitor_id non-nullable
    op.alter_column('post_views', 'visitor_id', nullable=False)

    # Drop old unique constraint and ip_address column
    op.drop_constraint('uq_post_view_ip', 'post_views', type_='unique')
    op.drop_column('post_views', 'ip_address')

    # Add composite index for time-window deduplication lookups
    op.create_index('ix_post_views_dedup', 'post_views', ['post_id', 'visitor_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('ix_post_views_dedup', table_name='post_views')
    op.add_column('post_views', sa.Column('ip_address', sa.String(45), nullable=True))
    op.execute("UPDATE post_views SET ip_address = visitor_id WHERE ip_address IS NULL")
    op.alter_column('post_views', 'ip_address', nullable=False)
    op.drop_column('post_views', 'visitor_id')
    op.create_unique_constraint('uq_post_view_ip', 'post_views', ['post_id', 'ip_address'])
