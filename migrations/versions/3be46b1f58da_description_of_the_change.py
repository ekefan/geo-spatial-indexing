"""description of the change

Revision ID: 3be46b1f58da
Revises: 
Create Date: 2026-09-06 18:21:30.775710

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = '3be46b1f58da'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table(
        'geo_buckets',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('h3_index', sa.String(length=15), nullable=False),
        sa.Column('centroid', geoalchemy2.types.Geography(geometry_type='POINT', srid=4326), nullable=False),
        sa.Column('boundary', geoalchemy2.types.Geography(geometry_type='POLYGON', srid=4326), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('h3_index'),
    )

    op.create_table(
        'bucket_aliases',
        sa.Column('bucket_id', sa.Uuid(), nullable=False),
        sa.Column('alias', sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(['bucket_id'], ['geo_buckets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('bucket_id', 'alias'),
    )
    op.create_index('ix_bucket_aliases_alias', 'bucket_aliases', ['alias'], unique=False)
    op.create_index(
        'ix_bucket_aliases_alias_trgm', 'bucket_aliases', ['alias'],
        unique=False, postgresql_using='gin', postgresql_ops={'alias': 'gin_trgm_ops'},
    )

    op.create_table(
        'properties',
        sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('bucket_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('location_name', sa.Text(), nullable=False),
        sa.Column('lat', sa.Double(), nullable=False),
        sa.Column('lng', sa.Double(), nullable=False),
        sa.Column('price', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.Text(), nullable=False),
        sa.Column('currency_unit_multiplier', sa.Integer(), nullable=False),
        sa.Column('bedrooms', sa.Integer(), nullable=False),
        sa.Column('bathrooms', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('bathrooms >= 0', name='ck_properties_bathrooms'),
        sa.CheckConstraint('bedrooms >= 0', name='ck_properties_bedrooms'),
        sa.CheckConstraint('currency_unit_multiplier > 0', name='ck_properties_currency_multiplier'),
        sa.CheckConstraint('lat >= -90 AND lat <= 90', name='ck_properties_lat'),
        sa.CheckConstraint('lng >= -180 AND lng <= 180', name='ck_properties_lng'),
        sa.CheckConstraint('price >= 0', name='ck_properties_price'),
        sa.ForeignKeyConstraint(['bucket_id'], ['geo_buckets.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_properties_bucket_created_id', 'properties', ['bucket_id', 'created_at', 'id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_properties_bucket_created_id', table_name='properties')
    op.drop_table('properties')

    op.drop_index('ix_bucket_aliases_alias_trgm', table_name='bucket_aliases')
    op.drop_index('ix_bucket_aliases_alias', table_name='bucket_aliases')
    op.drop_table('bucket_aliases')

    op.drop_table('geo_buckets')

    op.execute("DROP EXTENSION IF EXISTS pg_trgm")