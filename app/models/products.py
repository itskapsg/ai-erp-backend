"""
Product Models for Textile Order System

Implements complex product variations using JSONB for flexible attribute storage.
Supports textile-specific attributes like Color, Size, Fabric, Gold_Work, etc.

Key Features:
- Product: Base product with approval workflow
- ProductVariant: JSONB attributes for flexible textile variations
- Price adjustments per variant
- Stock management per variant
"""

from decimal import Decimal
from typing import Dict, Any, Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, Integer, ForeignKey, UniqueConstraint, DECIMAL, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.core import Base, ApprovalMixin
from app.models.utils import GUID, JSONB


class Product(Base, ApprovalMixin):
    """
    Product Master for Textile Items
    
    Represents the base product (e.g., "Banarasi Saree Design 101")
    Inherits ApprovalMixin for workflow management - new designs need approval
    """
    __tablename__ = "products"
    
    # Core product information
    id = Column(GUID(), primary_key=True, default=uuid4, index=True)
    name = Column(String(200), nullable=False, index=True, comment="Product name (e.g., 'Banarasi Saree Design 101')")
    base_price = Column(DECIMAL(10, 2), nullable=False, comment="Base price before variant adjustments")
    description = Column(Text, nullable=True, comment="Detailed product description")
    category = Column(String(100), nullable=False, index=True, comment="Product category (e.g., 'Sarees', 'Suits')")
    
    # Relationships
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', category='{self.category}')>"
    
    @property
    def variant_count(self) -> int:
        """Get the number of variants for this product"""
        return len(self.variants)
    
    @property
    def price_range(self) -> Dict[str, Decimal]:
        """Get the price range across all variants"""
        if not self.variants:
            return {"min": self.base_price, "max": self.base_price}
        
        prices = [self.base_price + (variant.price_adjustment or Decimal('0.00')) for variant in self.variants]
        return {
            "min": min(prices),
            "max": max(prices)
        }


class ProductVariant(Base):
    """
    Product Variant with JSONB Attributes
    
    Stores textile-specific variations using flexible JSONB structure.
    Examples:
    - {"Color": "Red", "Fabric": "Silk", "Size": "Free", "Gold_Work": "High"}
    - {"Color": "Blue", "Fabric": "Cotton", "Size": "M", "Border": "Traditional"}
    """
    __tablename__ = "product_variants"
    
    # Core variant information
    id = Column(GUID(), primary_key=True, default=uuid4, index=True)
    product_id = Column(GUID(), ForeignKey("products.id"), nullable=False, index=True)
    sku = Column(String(100), nullable=False, unique=True, index=True, comment="Stock Keeping Unit - unique identifier")
    
    # JSONB attributes for flexible textile variations
    attributes = Column(
        JSONB, 
        nullable=False, 
        default=dict,
        comment="Flexible attributes: {\"Color\": \"Red\", \"Fabric\": \"Silk\", \"Size\": \"Free\"}"
    )
    
    # Pricing and inventory
    price_adjustment = Column(
        DECIMAL(10, 2), 
        nullable=False, 
        default=Decimal('0.00'),
        comment="Price adjustment from base price (can be positive or negative)"
    )
    stock_quantity = Column(Integer, nullable=False, default=0, comment="Current stock quantity")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="variants")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('product_id', 'attributes', name='uq_product_variant_attributes'),
    )
    
    def __repr__(self):
        return f"<ProductVariant(id={self.id}, sku='{self.sku}', attributes={self.attributes})>"
    
    @property
    def final_price(self) -> Decimal:
        """Calculate the final price including adjustments"""
        return self.product.base_price + (self.price_adjustment or Decimal('0.00'))
    
    @property
    def is_in_stock(self) -> bool:
        """Check if variant is in stock"""
        return self.stock_quantity > 0
    
    def get_attribute(self, key: str, default: Any = None) -> Any:
        """Get a specific attribute value"""
        return self.attributes.get(key, default) if self.attributes else default
    
    def set_attribute(self, key: str, value: Any) -> None:
        """Set a specific attribute value"""
        if self.attributes is None:
            self.attributes = {}
        self.attributes[key] = value
    
    def update_attributes(self, new_attributes: Dict[str, Any]) -> None:
        """Update multiple attributes at once"""
        if self.attributes is None:
            self.attributes = {}
        self.attributes.update(new_attributes)
    
    def generate_sku(self) -> str:
        """Generate SKU based on product and attributes"""
        if not self.product or not self.attributes:
            return f"SKU-{str(self.id)[:8]}"
        
        # Create SKU from product name and key attributes
        product_code = self.product.name.replace(" ", "").upper()[:10]
        
        # Add key attributes to SKU
        attr_parts = []
        for key, value in sorted(self.attributes.items()):
            if isinstance(value, str) and len(value) > 0:
                attr_parts.append(f"{key[:3].upper()}{str(value)[:3].upper()}")
        
        attr_code = "-".join(attr_parts[:3])  # Limit to 3 attributes for readability
        
        return f"{product_code}-{attr_code}" if attr_code else f"{product_code}-{str(self.id)[:8]}"