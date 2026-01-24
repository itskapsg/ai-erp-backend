"""Add Orders and Order Items tables

Revision ID: simple_orders
Revises: 6d97f922cd61
Create Date: 2026-01-24 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'simple_orders'
down_revision: Union[str, Sequence[str], None] = '6d97f922cd61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create OrderStatus enum
    op.execute("CREATE TYPE orderstatus AS ENUM ('DRAFT', 'CONFIRMED', 'CANCELLED')")
    
    # Create orders table using raw SQL to avoid enum issues
    op.execute("""
        CREATE TABLE orders (
            id UUID PRIMARY KEY,
            order_number VARCHAR(20) NOT NULL UNIQUE,
            buyer_id UUID NOT NULL REFERENCES partners(id),
            seller_id UUID NOT NULL REFERENCES partners(id),
            total_amount NUMERIC(15,2) NOT NULL,
            status orderstatus NOT NULL,
            workflow_stage workflowstage NOT NULL,
            approved_by_id UUID REFERENCES users(id),
            rejection_reason TEXT,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP NOT NULL
        )
    """)
    
    op.create_index(op.f('ix_orders_order_number'), 'orders', ['order_number'], unique=True)
    
    # Create order_items table
    op.execute("""
        CREATE TABLE order_items (
            id UUID PRIMARY KEY,
            order_id UUID NOT NULL REFERENCES orders(id),
            product_variant_id UUID NOT NULL REFERENCES product_variants(id),
            quantity INTEGER NOT NULL,
            price NUMERIC(15,2) NOT NULL
        )
    """)


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP TABLE IF EXISTS order_items")
    op.drop_index(op.f('ix_orders_order_number'), table_name='orders')
    op.execute("DROP TABLE IF EXISTS orders")
    op.execute("DROP TYPE IF EXISTS orderstatus")