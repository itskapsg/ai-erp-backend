
import api from '@/api/axios';
import { Partner, Product, Order, Invoice, LedgerEntry } from '@/types';

export const DataService = {
    getPartners: async (type?: 'CUSTOMER' | 'SUPPLIER'): Promise<Partner[]> => {
        const params = type ? { type } : {};
        return api.get('/partners', { params });
    },

    getProducts: async (sellerId: string): Promise<Product[]> => {
        return api.get('/products', { params: { seller_id: sellerId } });
    },

    createOrder: async (orderData: any): Promise<Order> => {
        return api.post('/orders', orderData);
    },

    getInvoices: async (): Promise<Invoice[]> => {
        // Mock or implement endpoint
        return [];
    },

    reconcileInvoice: async (id: string): Promise<any> => {
        return api.post(`/accounting/invoices/${id}/reconcile`);
    },

    getLedger: async (partnerId: string): Promise<LedgerEntry[]> => {
        // Need an endpoint for this
        return [];
    }
};
