"""
PDF Service for generating professional Order Confirmation PDFs.

This service creates well-formatted PDF documents for order confirmations
with company branding, order details, and professional layout.
"""

from io import BytesIO
from datetime import datetime
from decimal import Decimal
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.models.orders import Order


class PDFService:
    """Service for generating PDF documents."""
    
    # Company Information
    COMPANY_NAME = "JGandhi Tex Pvt Ltd"
    COMPANY_ADDRESS = [
        "123 Textile Hub, Ring Road",
        "Surat, Gujarat - 395007",
        "India"
    ]
    COMPANY_CONTACT = [
        "Phone: +91 261 123 4567",
        "Email: orders@jgandhitex.com",
        "GST: 24ABCDE1234F1Z5"
    ]
    
    def __init__(self):
        """Initialize PDF service with styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        # Company name style
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=6,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
        
        # Company address style
        self.styles.add(ParagraphStyle(
            name='CompanyAddress',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_CENTER,
            spaceAfter=12,
            textColor=colors.grey
        ))
        
        # Document title style
        self.styles.add(ParagraphStyle(
            name='DocumentTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            textColor=colors.darkred,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            spaceAfter=6,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        ))
        
        # Party details style
        self.styles.add(ParagraphStyle(
            name='PartyDetails',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=3,
            leftIndent=12
        ))
        
        # Footer style
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors.grey
        ))
    
    def generate_order_pdf(self, order: Order) -> bytes:
        """
        Generate a professional PDF for an order confirmation.
        
        Args:
            order: Order object with all related data
            
        Returns:
            bytes: PDF file content as bytes
        """
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Build PDF content
        story = []
        
        # Header section
        story.extend(self._build_header())
        
        # Document title
        story.extend(self._build_title(order))
        
        # Order information
        story.extend(self._build_order_info(order))
        
        # Party details
        story.extend(self._build_party_details(order))
        
        # Order items table
        story.extend(self._build_items_table(order))
        
        # Order summary
        story.extend(self._build_order_summary(order))
        
        # Footer
        story.extend(self._build_footer())
        
        # Build PDF
        doc.build(story)
        
        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        return pdf_bytes
    
    def _build_header(self) -> list:
        """Build company header section."""
        elements = []
        
        # Company name
        elements.append(Paragraph(self.COMPANY_NAME, self.styles['CompanyName']))
        
        # Company address
        address_text = "<br/>".join(self.COMPANY_ADDRESS + self.COMPANY_CONTACT)
        elements.append(Paragraph(address_text, self.styles['CompanyAddress']))
        
        # Horizontal line
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.darkblue))
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _build_title(self, order: Order) -> list:
        """Build document title section."""
        elements = []
        
        title = f"ORDER CONFIRMATION<br/>Order #{order.order_number}"
        elements.append(Paragraph(title, self.styles['DocumentTitle']))
        elements.append(Spacer(1, 12))
        
        return elements
    
    def _build_order_info(self, order: Order) -> list:
        """Build order information section."""
        elements = []
        
        # Order info table
        order_date = order.created_at.strftime("%d %B %Y")
        order_time = order.created_at.strftime("%I:%M %p")
        
        order_info_data = [
            ['Order Date:', order_date, 'Order Time:', order_time],
            ['Status:', order.status.value.title(), 'Workflow:', order.workflow_stage.value.replace('_', ' ').title()]
        ]
        
        order_info_table = Table(order_info_data, colWidths=[1.2*inch, 1.5*inch, 1.2*inch, 1.5*inch])
        order_info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # First column bold
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),  # Third column bold
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(order_info_table)
        elements.append(Spacer(1, 18))
        
        return elements
    
    def _build_party_details(self, order: Order) -> list:
        """Build buyer and seller details section."""
        elements = []
        
        # Create two-column layout for buyer and seller
        party_data = []
        
        # Headers
        party_data.append([
            Paragraph('<b>BUYER DETAILS</b>', self.styles['SectionHeader']),
            Paragraph('<b>SELLER DETAILS</b>', self.styles['SectionHeader'])
        ])
        
        # Buyer details
        buyer_details = [
            f"<b>{order.buyer.name}</b>",
            f"Type: {order.buyer.type.value.title()}",
            f"GST: {order.buyer.gst_number}",
            f"Credit Limit: ₹{order.buyer.credit_limit:,.2f}"
        ]
        
        # Seller details
        seller_details = [
            f"<b>{order.seller.name}</b>",
            f"Type: {order.seller.type.value.title()}",
            f"GST: {order.seller.gst_number}",
            f"Credit Limit: ₹{order.seller.credit_limit:,.2f}"
        ]
        
        # Add details rows
        party_data.append([
            Paragraph("<br/>".join(buyer_details), self.styles['PartyDetails']),
            Paragraph("<br/>".join(seller_details), self.styles['PartyDetails'])
        ])
        
        party_table = Table(party_data, colWidths=[3*inch, 3*inch])
        party_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
        ]))
        
        elements.append(party_table)
        elements.append(Spacer(1, 18))
        
        return elements
    
    def _build_items_table(self, order: Order) -> list:
        """Build order items table."""
        elements = []
        
        # Table headers
        headers = ['S.No', 'Item Name', 'Variant Details', 'Qty', 'Unit Price', 'Line Total']
        
        # Table data
        table_data = [headers]
        
        for idx, item in enumerate(order.items, 1):
            # Get product and variant details
            variant = item.product_variant
            product = variant.product
            
            # Format variant attributes
            variant_details = []
            if variant.attributes:
                for key, value in variant.attributes.items():
                    variant_details.append(f"{key}: {value}")
            variant_text = "\n".join(variant_details) if variant_details else "Standard"
            
            # Add row
            table_data.append([
                str(idx),
                product.name,
                variant_text,
                str(item.quantity),
                f"₹{item.price:,.2f}",
                f"₹{item.line_total:,.2f}"
            ])
        
        # Create table
        items_table = Table(table_data, colWidths=[0.5*inch, 2*inch, 1.5*inch, 0.7*inch, 1*inch, 1*inch])
        
        # Table style
        items_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S.No center
            ('ALIGN', (1, 1), (2, -1), 'LEFT'),    # Item name and variant left
            ('ALIGN', (3, 1), (-1, -1), 'RIGHT'),  # Numbers right
            
            # Grid and padding
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            
            # Alternating row colors
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(Paragraph('<b>ORDER ITEMS</b>', self.styles['SectionHeader']))
        elements.append(Spacer(1, 6))
        elements.append(items_table)
        elements.append(Spacer(1, 18))
        
        return elements
    
    def _build_order_summary(self, order: Order) -> list:
        """Build order summary section."""
        elements = []
        
        # Calculate totals
        subtotal = order.total_amount
        tax_rate = Decimal('0.18')  # 18% GST
        tax_amount = subtotal * tax_rate
        total_amount = subtotal + tax_amount
        
        # Summary data
        summary_data = [
            ['', '', '', 'Subtotal:', f"₹{subtotal:,.2f}"],
            ['', '', '', 'GST (18%):', f"₹{tax_amount:,.2f}"],
            ['', '', '', '', ''],  # Empty row for spacing
            ['', '', '', 'TOTAL AMOUNT:', f"₹{total_amount:,.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[0.5*inch, 2*inch, 1.5*inch, 1.2*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
            ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),  # Total row bold
            ('FONTSIZE', (3, -1), (-1, -1), 12),  # Total row larger
            ('LINEABOVE', (3, -1), (-1, -1), 2, colors.darkblue),  # Line above total
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(summary_table)
        elements.append(Spacer(1, 24))
        
        return elements
    
    def _build_footer(self) -> list:
        """Build footer section."""
        elements = []
        
        # Signature section
        signature_data = [
            ['', 'Authorized Signatory'],
            ['Customer Signature', 'JGandhi Tex Pvt Ltd']
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(signature_table)
        elements.append(Spacer(1, 24))
        
        # Thank you message
        thank_you = "Thank you for your business!<br/>For any queries, please contact us at orders@jgandhitex.com"
        elements.append(Paragraph(thank_you, self.styles['Footer']))
        
        # Generation timestamp
        timestamp = f"Generated on: {datetime.now().strftime('%d %B %Y at %I:%M %p')}"
        elements.append(Spacer(1, 12))
        elements.append(Paragraph(timestamp, self.styles['Footer']))
        
        return elements


# Global instance
pdf_service = PDFService()