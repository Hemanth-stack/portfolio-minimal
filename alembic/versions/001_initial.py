"""Initial schema with categories

Revision ID: 001_initial
Revises: 
Create Date: 2025-12-26

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Categories
    op.create_table(
        'categories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('slug', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('description', sa.String(300), default=''),
    )
    
    # Tags
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(50), unique=True, nullable=False),
        sa.Column('slug', sa.String(50), unique=True, nullable=False, index=True),
    )
    
    # Posts
    op.create_table(
        'posts',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), unique=True, nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('excerpt', sa.String(500), default=''),
        sa.Column('published', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Post tags (many-to-many)
    op.create_table(
        'post_tags',
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('tag_id', sa.Integer(), sa.ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True),
    )
    
    # Post categories (many-to-many)
    op.create_table(
        'post_categories',
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('category_id', sa.Integer(), sa.ForeignKey('categories.id', ondelete='CASCADE'), primary_key=True),
    )
    
    # Comments
    op.create_table(
        'comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('post_id', sa.Integer(), sa.ForeignKey('posts.id', ondelete='CASCADE'), nullable=False),
        sa.Column('author_name', sa.String(100), nullable=False),
        sa.Column('author_email', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('approved', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Projects
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(200), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('short_description', sa.String(300), default=''),
        sa.Column('tech_stack', sa.String(500), default=''),
        sa.Column('metrics', sa.String(500), default=''),
        sa.Column('github_url', sa.String(500), nullable=True),
        sa.Column('live_url', sa.String(500), nullable=True),
        sa.Column('featured', sa.Boolean(), default=False),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # Pages
    op.create_table(
        'pages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('slug', sa.String(50), unique=True, nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('meta_description', sa.String(300), default=''),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # Sections (for inline editing)
    op.create_table(
        'sections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('page', sa.String(50), nullable=False, index=True),
        sa.Column('section_key', sa.String(100), nullable=False, index=True),
        sa.Column('title', sa.String(200), default=''),
        sa.Column('content', sa.Text(), default=''),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('visible', sa.Boolean(), default=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.UniqueConstraint('page', 'section_key', name='uq_page_section_key'),
    )
    
    # Site settings
    op.create_table(
        'site_settings',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('key', sa.String(100), unique=True, nullable=False, index=True),
        sa.Column('value', sa.Text(), default=''),
        sa.Column('description', sa.String(300), default=''),
    )
    
    # Resume sections
    op.create_table(
        'resume_sections',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('section_type', sa.String(50), nullable=False),
        sa.Column('title', sa.String(200), default=''),
        sa.Column('content', sa.Text(), default=''),
        sa.Column('order', sa.Integer(), default=0),
        sa.Column('visible', sa.Boolean(), default=True),
    )
    
    # Contact messages
    op.create_table(
        'contact_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('email', sa.String(200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('read', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('contact_messages')
    op.drop_table('resume_sections')
    op.drop_table('site_settings')
    op.drop_table('sections')
    op.drop_table('pages')
    op.drop_table('projects')
    op.drop_table('comments')
    op.drop_table('post_categories')
    op.drop_table('post_tags')
    op.drop_table('posts')
    op.drop_table('tags')
    op.drop_table('categories')
