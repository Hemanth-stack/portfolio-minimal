"""Add post_views table for IP-based unique view tracking

Revision ID: 004_add_post_views_table
Revises: 003_add_view_and_like_counts
Create Date: 2026-03-06

"""
from alembic import op
import sqlalchemy as sa

revision = '004_add_post_views_table'
down_revision = '003_add_view_and_like_counts'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'post_views',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.UniqueConstraint('post_id', 'ip_address', name='uq_post_view_ip'),
    )


def downgrade() -> None:
    op.drop_table('post_views')
