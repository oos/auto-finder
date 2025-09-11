"""Initial database migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=128), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('min_price', sa.Integer(), nullable=True),
        sa.Column('max_price', sa.Integer(), nullable=True),
        sa.Column('approved_locations', sa.Text(), nullable=True),
        sa.Column('max_pages_per_site', sa.Integer(), nullable=True),
        sa.Column('min_deal_score', sa.Integer(), nullable=True),
        sa.Column('scrape_carzone', sa.Boolean(), nullable=True),
        sa.Column('scrape_donedeal', sa.Boolean(), nullable=True),
        sa.Column('scrape_adverts', sa.Boolean(), nullable=True),
        sa.Column('scrape_carsireland', sa.Boolean(), nullable=True),
        sa.Column('scrape_lewismotors', sa.Boolean(), nullable=True),
        sa.Column('weight_price_vs_market', sa.Integer(), nullable=True),
        sa.Column('weight_mileage_vs_year', sa.Integer(), nullable=True),
        sa.Column('weight_co2_tax_band', sa.Integer(), nullable=True),
        sa.Column('weight_popularity_rarity', sa.Integer(), nullable=True),
        sa.Column('weight_price_dropped', sa.Integer(), nullable=True),
        sa.Column('weight_location_match', sa.Integer(), nullable=True),
        sa.Column('weight_listing_freshness', sa.Integer(), nullable=True),
        sa.Column('email_notifications', sa.Boolean(), nullable=True),
        sa.Column('daily_email_time', sa.String(length=5), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create blacklists table
    op.create_table('blacklists',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('keyword', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create car_listings table
    op.create_table('car_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('price', sa.Integer(), nullable=False),
        sa.Column('location', sa.String(length=200), nullable=False),
        sa.Column('url', sa.String(length=1000), nullable=False),
        sa.Column('image_url', sa.String(length=1000), nullable=True),
        sa.Column('image_hash', sa.String(length=64), nullable=True),
        sa.Column('source_site', sa.String(length=50), nullable=False),
        sa.Column('make', sa.String(length=50), nullable=True),
        sa.Column('model', sa.String(length=100), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('mileage', sa.Integer(), nullable=True),
        sa.Column('fuel_type', sa.String(length=20), nullable=True),
        sa.Column('transmission', sa.String(length=20), nullable=True),
        sa.Column('co2_emissions', sa.Integer(), nullable=True),
        sa.Column('tax_band', sa.String(length=10), nullable=True),
        sa.Column('nct_expiry', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('is_duplicate', sa.Boolean(), nullable=True),
        sa.Column('duplicate_group_id', sa.Integer(), nullable=True),
        sa.Column('deal_score', sa.Float(), nullable=True),
        sa.Column('price_vs_market_score', sa.Float(), nullable=True),
        sa.Column('mileage_vs_year_score', sa.Float(), nullable=True),
        sa.Column('co2_tax_score', sa.Float(), nullable=True),
        sa.Column('popularity_rarity_score', sa.Float(), nullable=True),
        sa.Column('price_dropped_score', sa.Float(), nullable=True),
        sa.Column('location_match_score', sa.Float(), nullable=True),
        sa.Column('listing_freshness_score', sa.Float(), nullable=True),
        sa.Column('previous_price', sa.Integer(), nullable=True),
        sa.Column('price_dropped', sa.Boolean(), nullable=True),
        sa.Column('price_drop_amount', sa.Integer(), nullable=True),
        sa.Column('first_seen', sa.DateTime(), nullable=True),
        sa.Column('last_seen', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('url')
    )

    # Create scrape_logs table
    op.create_table('scrape_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('site_name', sa.String(length=50), nullable=False),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('listings_found', sa.Integer(), nullable=True),
        sa.Column('listings_new', sa.Integer(), nullable=True),
        sa.Column('listings_updated', sa.Integer(), nullable=True),
        sa.Column('listings_removed', sa.Integer(), nullable=True),
        sa.Column('pages_scraped', sa.Integer(), nullable=True),
        sa.Column('errors', sa.Text(), nullable=True),
        sa.Column('is_blocked', sa.Boolean(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create email_logs table
    op.create_table('email_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('subject', sa.String(length=200), nullable=False),
        sa.Column('listings_included', sa.Integer(), nullable=True),
        sa.Column('total_listings_scraped', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    # Drop tables in reverse order
    op.drop_table('email_logs')
    op.drop_table('scrape_logs')
    op.drop_table('car_listings')
    op.drop_table('blacklists')
    op.drop_table('user_settings')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
