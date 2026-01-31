
export interface Partner {
    id: string;
    name: string;
    type: 'CUSTOMER' | 'SUPPLIER';
    credit_limit: number;
    outstanding_balance: number;
    commission_rate: number;
}

export interface ProductVariant {
    id: string;
    sku: string;
    price_adjustment: number;
    attributes: Record<string, any>;
}

export interface Product {
    id: string;
    name: string;
    seller_id: string;
    base_price: number;
    category: string;
    variants: ProductVariant[];
    design_number: string; // Critical for Textile
}

export interface OrderItem {
    id?: string;
    variant_id: string;
    quantity: number;
    price: number;
    line_total?: number;
}

export interface Order {
    id: string;
    order_number: string;
    buyer_id: string;
    seller_id: string;
    total_amount: number;
    status: 'draft' | 'pending_approval' | 'confirmed' | 'invoiced' | 'payment_received' | 'cancelled';
    items: OrderItem[];
    created_at: string;
}

export interface Invoice {
    id: string;
    invoice_number: string;
    supplier_id: string;
    date: string;
    total_amount: number;
    order_id: string;
    status: 'draft' | 'reconciled' | 'disputed';
}

export interface LedgerEntry {
    id: string;
    transaction_date: string;
    description: string;
    debit: number;
    credit: number;
    balance: number;
    reference_id: string;
}
