"""Remove subject column from contact_messages

Revision ID: 002_remove_subject
Revises: 001_initial
Create Date: 2025-12-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_remove_subject'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make subject column nullable (safer than dropping)
    op.alter_column('contact_messages', 'subject',
                    existing_type=sa.String(300),
                    nullable=True)


def downgrade() -> None:
    # Revert to NOT NULL
    op.alter_column('contact_messages', 'subject',
                    existing_type=sa.String(300),
                    nullable=False,
                    server_default='')
