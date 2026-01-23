"""Add Partners and Approval Policy

Revision ID: cde0239b0088
Revises: 2dcfbfc0c3d6
Create Date: 2026-01-23 11:20:17.464329

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cde0239b0088'
down_revision: Union[str, Sequence[str], None] = '2dcfbfc0c3d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create approval_policies table
    op.create_table('approval_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('required_role', sa.Enum('ADMIN', 'MANAGER', 'ACCOUNTANT', 'SALESMAN', name='userrole'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_approval_policies_action'), 'approval_policies', ['action'], unique=False)
    op.create_index(op.f('ix_approval_policies_resource'), 'approval_policies', ['resource'], unique=False)
    
    # Create partners table
    op.create_table('partners',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('type', sa.Enum('CUSTOMER', 'SUPPLIER', name='partnertype'), nullable=False),
        sa.Column('gst_number', sa.String(length=15), nullable=True),
        sa.Column('credit_limit', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('workflow_stage', sa.Enum('DRAFT', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED', name='workflowstage'), nullable=False),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gst_number')
    )
    op.create_index(op.f('ix_partners_gst_number'), 'partners', ['gst_number'], unique=False)
    op.create_index(op.f('ix_partners_name'), 'partners', ['name'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop partners table
    op.drop_index(op.f('ix_partners_name'), table_name='partners')
    op.drop_index(op.f('ix_partners_gst_number'), table_name='partners')
    op.drop_table('partners')
    
    # Drop approval_policies table
    op.drop_index(op.f('ix_approval_policies_resource'), table_name='approval_policies')
    op.drop_index(op.f('ix_approval_policies_action'), table_name='approval_policies')
    op.drop_table('approval_policies')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS partnertype')
    # Note: workflowstage and userrole enums are used by other tables, so we don't drop them
