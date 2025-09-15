"""Add notes column to scrape_logs table

Revision ID: 002_add_notes_column
Revises: 001_initial_migration
Create Date: 2025-09-13 10:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002_add_notes_column'
down_revision = '001_initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    """Add notes column to scrape_logs table"""
    try:
        op.add_column('scrape_logs', sa.Column('notes', sa.Text(), nullable=True))
        print("✅ Added notes column to scrape_logs table")
    except Exception as e:
        print(f"❌ Error adding notes column: {e}")
        # Column might already exist, which is fine
        pass

def downgrade():
    """Remove notes column from scrape_logs table"""
    try:
        op.drop_column('scrape_logs', 'notes')
        print("✅ Removed notes column from scrape_logs table")
    except Exception as e:
        print(f"❌ Error removing notes column: {e}")
        pass

