"""Add MealPlan table only

Revision ID: 05897c3b244d
Revises: 73c83786a214
Create Date: 2026-01-24 17:43:25.208132

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05897c3b244d'
down_revision: Union[str, Sequence[str], None] = '73c83786a214'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create DietType enum if not exists
    op.execute("DO $$ BEGIN CREATE TYPE diettype AS ENUM ('STANDARD', 'JAIN', 'VEG_ONLY', 'VEGAN'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create MealLocation enum if not exists
    op.execute("DO $$ BEGIN CREATE TYPE meallocation AS ENUM ('OFFICE', 'RESTAURANT', 'SUPPLIER', 'SKIP'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # Create meal_plans table
    op.create_table('meal_plans',
        sa.Column('id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visit_id', sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('diet', sa.Enum('STANDARD', 'JAIN', 'VEG_ONLY', 'VEGAN', name='diettype'), nullable=True),
        sa.Column('breakfast', sa.Boolean(), nullable=True),
        sa.Column('lunch', sa.Enum('OFFICE', 'RESTAURANT', 'SUPPLIER', 'SKIP', name='meallocation'), nullable=True),
        sa.Column('dinner', sa.Enum('OFFICE', 'RESTAURANT', 'SUPPLIER', 'SKIP', name='meallocation'), nullable=True),
        sa.Column('special_notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['visit_id'], ['visits.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('meal_plans')
    op.execute("DROP TYPE meallocation")
    op.execute("DROP TYPE diettype")
