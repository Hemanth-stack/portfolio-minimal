"""Add indexing_logs table

Revision ID: 005_add_indexing_logs
Revises: 004_add_post_views_table
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa

revision = '005_add_indexing_logs'
down_revision = '004_add_post_views_table'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'indexing_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('service', sa.String(20), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('indexing_logs')
