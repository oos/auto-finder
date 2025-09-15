"""Add port settings to user_settings

Revision ID: 002_add_port_settings
Revises: 001_initial_migration
Create Date: 2025-09-15 22:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_port_settings'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Add port configuration columns to user_settings table
    op.add_column('user_settings', sa.Column('frontend_port', sa.Integer(), nullable=True, default=3000))
    op.add_column('user_settings', sa.Column('backend_port', sa.Integer(), nullable=True, default=5003))
    
    # Set default values for existing records
    op.execute("UPDATE user_settings SET frontend_port = 3000 WHERE frontend_port IS NULL")
    op.execute("UPDATE user_settings SET backend_port = 5003 WHERE backend_port IS NULL")


def downgrade():
    # Remove port configuration columns
    op.drop_column('user_settings', 'backend_port')
    op.drop_column('user_settings', 'frontend_port')
