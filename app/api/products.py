"""
Products API Endpoints

Implements CRUD operations for products and variants with integrated approval workflow.
Supports complex textile variations using JSONB attributes.

Key Features:
- Product creation with approval workflow
- Flexible variant management with JSONB attributes
- Price calculations with adjustments
- Stock management
- Textile-specific attribute handling
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.models import Product, ProductVariant, User, UserRole, WorkflowStage
from app.services.approval_service import ApprovalService
from app.database import get_db
from app.api.auth import get_current_active_user, require_role


# Router
router = APIRouter(prefix="/api/v1/products", tags=["products"])


# Pydantic Models
class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Product name")
    base_price: Decimal = Field(..., ge=0, description="Base price before variant adjustments")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(..., min_length=1, max_length=100, description="Product category")


class ProductVariantCreate(BaseModel):
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit (auto-generated if not provided)")
    attributes: Dict[str, Any] = Field(..., description="Variant attributes as JSON object")
    price_adjustment: Optional[Decimal] = Field(Decimal('0.00'), description="Price adjustment from base price")
    stock_quantity: int = Field(0, ge=0, description="Initial stock quantity")
    
    @validator('attributes')
    def validate_attributes(cls, v):
        if not isinstance(v, dict) or len(v) == 0:
            raise ValueError('Attributes must be a non-empty dictionary')
        
        # Validate common textile attributes
        valid_keys = {'Color', 'Fabric', 'Size', 'Gold_Work', 'Border', 'Pattern', 'Length', 'Width', 'Weight'}
        for key in v.keys():
            if not isinstance(key, str) or len(key.strip()) == 0:
                raise ValueError(f'Attribute key must be a non-empty string: {key}')
        
        return v


class ProductVariantResponse(BaseModel):
    id: str
    product_id: str
    sku: str
    attributes: Dict[str, Any]
    price_adjustment: Decimal
    stock_quantity: int
    final_price: Decimal
    is_in_stock: bool
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    id: str
    name: str
    base_price: Decimal
    description: Optional[str]
    category: str
    variant_count: int
    price_range: Dict[str, Decimal]
    workflow_stage: str
    approved_by_id: Optional[str]
    rejection_reason: Optional[str]
    created_at: str
    updated_at: str
    variants: Optional[List[ProductVariantResponse]] = None

    class Config:
        from_attributes = True


class ProductVariantUpdate(BaseModel):
    attributes: Optional[Dict[str, Any]] = None
    price_adjustment: Optional[Decimal] = None
    stock_quantity: Optional[int] = Field(None, ge=0)


# API Endpoints
@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new product
    
    CRITICAL: Uses ApprovalService to determine workflow stage based on policies!
    - If approval required: Creates product with PENDING_APPROVAL status
    - If auto-approved: Creates product with APPROVED status
    """
    
    # Initialize approval service
    approval_service = ApprovalService(db)
    
    # CRITICAL: Check approval policy and determine workflow stage
    workflow_stage = approval_service.determine_workflow_stage('product', 'create', current_user)
    
    # Check for duplicate product name in same category
    existing_product = db.query(Product).filter(
        Product.name == product_data.name,
        Product.category == product_data.category
    ).first()
    
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product '{product_data.name}' already exists in category '{product_data.category}'"
        )
    
    # Create product with determined workflow stage
    product = Product(
        name=product_data.name,
        base_price=product_data.base_price,
        description=product_data.description,
        category=product_data.category,
        workflow_stage=workflow_stage  # Set by ApprovalService!
    )
    
    # If auto-approved, set the approver
    if workflow_stage == WorkflowStage.APPROVED:
        product.approved_by_id = current_user.id
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return ProductResponse(
        id=str(product.id),
        name=product.name,
        base_price=product.base_price,
        description=product.description,
        category=product.category,
        variant_count=product.variant_count,
        price_range=product.price_range,
        workflow_stage=product.workflow_stage.value,
        approved_by_id=str(product.approved_by_id) if product.approved_by_id else None,
        rejection_reason=product.rejection_reason,
        created_at=product.created_at.isoformat(),
        updated_at=product.updated_at.isoformat(),
        variants=[]
    )


@router.post("/{product_id}/variants/", response_model=ProductVariantResponse, status_code=status.HTTP_201_CREATED)
async def create_product_variant(
    product_id: UUID,
    variant_data: ProductVariantCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a variant to an existing product
    
    Creates a new variant with JSONB attributes for flexible textile variations.
    """
    
    # Find the product
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if product is approved (can only add variants to approved products)
    if product.workflow_stage != WorkflowStage.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot add variants to product with status: {product.workflow_stage.value}"
        )
    
    # Check for duplicate variant attributes
    existing_variant = db.query(ProductVariant).filter(
        ProductVariant.product_id == product_id,
        ProductVariant.attributes == variant_data.attributes
    ).first()
    
    if existing_variant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A variant with these attributes already exists for this product"
        )
    
    # Create the variant
    variant = ProductVariant(
        product_id=product_id,
        attributes=variant_data.attributes,
        price_adjustment=variant_data.price_adjustment or Decimal('0.00'),
        stock_quantity=variant_data.stock_quantity
    )
    
    # Generate SKU if not provided
    if variant_data.sku:
        # Check if SKU is unique
        existing_sku = db.query(ProductVariant).filter(ProductVariant.sku == variant_data.sku).first()
        if existing_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU '{variant_data.sku}' already exists"
            )
        variant.sku = variant_data.sku
    else:
        # Auto-generate SKU based on product and attributes
        product_code = product.name.replace(" ", "").upper()[:10]
        
        # Add key attributes to SKU
        attr_parts = []
        for key, value in sorted(variant_data.attributes.items()):
            if isinstance(value, str) and len(value) > 0:
                attr_parts.append(f"{key[:3].upper()}{str(value)[:3].upper()}")
        
        attr_code = "-".join(attr_parts[:3])  # Limit to 3 attributes for readability
        base_sku = f"{product_code}-{attr_code}" if attr_code else f"{product_code}-{str(variant.id)[:8]}"
        
        # Ensure uniqueness
        counter = 1
        test_sku = base_sku
        while db.query(ProductVariant).filter(ProductVariant.sku == test_sku).first():
            test_sku = f"{base_sku}-{counter}"
            counter += 1
        
        variant.sku = test_sku
    
    db.add(variant)
    db.commit()
    db.refresh(variant)
    
    return ProductVariantResponse(
        id=str(variant.id),
        product_id=str(variant.product_id),
        sku=variant.sku,
        attributes=variant.attributes,
        price_adjustment=variant.price_adjustment,
        stock_quantity=variant.stock_quantity,
        final_price=variant.final_price,
        is_in_stock=variant.is_in_stock,
        created_at=variant.created_at.isoformat(),
        updated_at=variant.updated_at.isoformat()
    )


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    workflow_stage: Optional[WorkflowStage] = None,
    include_variants: bool = Query(False, description="Include variant details in response"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all products with optional filtering
    
    Query parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - category: Filter by product category
    - workflow_stage: Filter by workflow stage
    - include_variants: Include variant details in response
    """
    
    query = db.query(Product)
    
    # Apply filters
    if category:
        query = query.filter(Product.category == category)
    
    if workflow_stage:
        query = query.filter(Product.workflow_stage == workflow_stage)
    
    # Apply pagination
    products = query.offset(skip).limit(limit).all()
    
    # Build response
    result = []
    for product in products:
        variants = None
        if include_variants:
            variants = [
                ProductVariantResponse(
                    id=str(variant.id),
                    product_id=str(variant.product_id),
                    sku=variant.sku,
                    attributes=variant.attributes,
                    price_adjustment=variant.price_adjustment,
                    stock_quantity=variant.stock_quantity,
                    final_price=variant.final_price,
                    is_in_stock=variant.is_in_stock,
                    created_at=variant.created_at.isoformat(),
                    updated_at=variant.updated_at.isoformat()
                )
                for variant in product.variants
            ]
        
        result.append(ProductResponse(
            id=str(product.id),
            name=product.name,
            base_price=product.base_price,
            description=product.description,
            category=product.category,
            variant_count=product.variant_count,
            price_range=product.price_range,
            workflow_stage=product.workflow_stage.value,
            approved_by_id=str(product.approved_by_id) if product.approved_by_id else None,
            rejection_reason=product.rejection_reason,
            created_at=product.created_at.isoformat(),
            updated_at=product.updated_at.isoformat(),
            variants=variants
        ))
    
    return result


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    include_variants: bool = Query(True, description="Include variant details in response"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific product by ID with optional variant details"""
    
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    variants = None
    if include_variants:
        variants = [
            ProductVariantResponse(
                id=str(variant.id),
                product_id=str(variant.product_id),
                sku=variant.sku,
                attributes=variant.attributes,
                price_adjustment=variant.price_adjustment,
                stock_quantity=variant.stock_quantity,
                final_price=variant.final_price,
                is_in_stock=variant.is_in_stock,
                created_at=variant.created_at.isoformat(),
                updated_at=variant.updated_at.isoformat()
            )
            for variant in product.variants
        ]
    
    return ProductResponse(
        id=str(product.id),
        name=product.name,
        base_price=product.base_price,
        description=product.description,
        category=product.category,
        variant_count=product.variant_count,
        price_range=product.price_range,
        workflow_stage=product.workflow_stage.value,
        approved_by_id=str(product.approved_by_id) if product.approved_by_id else None,
        rejection_reason=product.rejection_reason,
        created_at=product.created_at.isoformat(),
        updated_at=product.updated_at.isoformat(),
        variants=variants
    )


@router.get("/{product_id}/variants/", response_model=List[ProductVariantResponse])
async def list_product_variants(
    product_id: UUID,
    in_stock_only: bool = Query(False, description="Show only variants with stock > 0"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all variants for a specific product"""
    
    # Verify product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    query = db.query(ProductVariant).filter(ProductVariant.product_id == product_id)
    
    if in_stock_only:
        query = query.filter(ProductVariant.stock_quantity > 0)
    
    variants = query.all()
    
    return [
        ProductVariantResponse(
            id=str(variant.id),
            product_id=str(variant.product_id),
            sku=variant.sku,
            attributes=variant.attributes,
            price_adjustment=variant.price_adjustment,
            stock_quantity=variant.stock_quantity,
            final_price=variant.final_price,
            is_in_stock=variant.is_in_stock,
            created_at=variant.created_at.isoformat(),
            updated_at=variant.updated_at.isoformat()
        )
        for variant in variants
    ]


@router.put("/{product_id}/variants/{variant_id}", response_model=ProductVariantResponse)
async def update_product_variant(
    product_id: UUID,
    variant_id: UUID,
    variant_update: ProductVariantUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a product variant"""
    
    # Find the variant
    variant = db.query(ProductVariant).filter(
        ProductVariant.id == variant_id,
        ProductVariant.product_id == product_id
    ).first()
    
    if not variant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product variant not found"
        )
    
    # Update fields
    if variant_update.attributes is not None:
        variant.attributes = variant_update.attributes
    
    if variant_update.price_adjustment is not None:
        variant.price_adjustment = variant_update.price_adjustment
    
    if variant_update.stock_quantity is not None:
        variant.stock_quantity = variant_update.stock_quantity
    
    db.commit()
    db.refresh(variant)
    
    return ProductVariantResponse(
        id=str(variant.id),
        product_id=str(variant.product_id),
        sku=variant.sku,
        attributes=variant.attributes,
        price_adjustment=variant.price_adjustment,
        stock_quantity=variant.stock_quantity,
        final_price=variant.final_price,
        is_in_stock=variant.is_in_stock,
        created_at=variant.created_at.isoformat(),
        updated_at=variant.updated_at.isoformat()
    )