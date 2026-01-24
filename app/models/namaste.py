"""
Project Namaste - Customer Visit Management Models

This module handles Customer Arrivals, Accommodation (Guest House/Hotel), 
Logistics, and Supplier Itineraries for business visits.

Key Features:
- Visit: Customer visit scheduling and tracking
- Accommodation: Guest house bed management and hotel bookings
- Transport: Pickup/drop logistics with driver coordination
- ItineraryItem: Supplier meeting appointments and scheduling
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.core import Base, ApprovalMixin


class VisitStatus(Enum):
    """Visit status enumeration"""
    SCHEDULED = "scheduled"
    ONGOING = "ongoing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class VisitMode(Enum):
    """Visit mode enumeration"""
    ACCOMPANIED = "accompanied"  # With salesperson guide
    SOLO = "solo"               # Customer visits alone


class AccommodationType(Enum):
    """Accommodation type enumeration"""
    OFFICE_GUEST_HOUSE = "office_guest_house"
    HOTEL = "hotel"
    SELF = "self"  # Customer arranges own accommodation


class TransportType(Enum):
    """Transport type enumeration"""
    PICKUP = "pickup"      # Airport/Station pickup
    DROP = "drop"          # Airport/Station drop
    MARKET_TOUR = "market_tour"  # Market/supplier tour


class TransportMode(Enum):
    """Transport mode enumeration"""
    COMPANY_DRIVER = "company_driver"
    TAXI = "taxi"
    AUTO = "auto"
    SELF = "self"  # Customer arranges own transport


class AppointmentStatus(Enum):
    """Appointment status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Visit(Base, ApprovalMixin):
    """
    Customer Visit Management
    
    Tracks customer visits including dates, accommodation, and logistics.
    Inherits ApprovalMixin for workflow management - visits may need approval.
    """
    __tablename__ = "visits"
    
    # Core visit information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False, index=True)
    salesperson_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Visit scheduling
    start_date = Column(DateTime, nullable=False, index=True, comment="Visit start date and time")
    end_date = Column(DateTime, nullable=False, index=True, comment="Visit end date and time")
    status = Column(SQLEnum(VisitStatus), nullable=False, default=VisitStatus.SCHEDULED, index=True)
    visit_mode = Column(SQLEnum(VisitMode), nullable=False, default=VisitMode.ACCOMPANIED)
    
    # Arrival details
    arrival_details = Column(Text, nullable=True, comment="Flight/train details, arrival time, etc.")
    ticket_url = Column(String(500), nullable=True, comment="URL to ticket/booking confirmation")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    customer = relationship("Partner", foreign_keys=[customer_id], backref="visits")
    salesperson = relationship("User", foreign_keys=[salesperson_id], backref="assigned_visits")
    accommodations = relationship("Accommodation", back_populates="visit", cascade="all, delete-orphan")
    transports = relationship("Transport", back_populates="visit", cascade="all, delete-orphan")
    itinerary_items = relationship("ItineraryItem", back_populates="visit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Visit(id={self.id}, customer='{self.customer.name if self.customer else 'Unknown'}', status='{self.status.value}')>"
    
    @property
    def duration_days(self) -> int:
        """Calculate visit duration in days"""
        if self.start_date and self.end_date:
            return (self.end_date.date() - self.start_date.date()).days + 1
        return 0
    
    @property
    def is_active(self) -> bool:
        """Check if visit is currently active"""
        return self.status in [VisitStatus.SCHEDULED, VisitStatus.ONGOING]
    
    @property
    def has_accommodation(self) -> bool:
        """Check if visit has accommodation arranged"""
        return len(self.accommodations) > 0
    
    @property
    def has_transport(self) -> bool:
        """Check if visit has transport arranged"""
        return len(self.transports) > 0


class Accommodation(Base):
    """
    Visit Accommodation Management
    
    Handles guest house bed assignments and hotel bookings for customer visits.
    """
    __tablename__ = "accommodations"
    
    # Core accommodation information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, index=True)
    type = Column(SQLEnum(AccommodationType), nullable=False, index=True)
    
    # Accommodation details
    details = Column(Text, nullable=True, comment="Hotel name, address, or guest house details")
    bed_assigned = Column(Integer, nullable=True, comment="Bed number (1-5) for office guest house")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    visit = relationship("Visit", back_populates="accommodations")
    
    def __repr__(self):
        bed_info = f", bed={self.bed_assigned}" if self.bed_assigned else ""
        return f"<Accommodation(id={self.id}, type='{self.type.value}'{bed_info})>"
    
    @property
    def is_guest_house(self) -> bool:
        """Check if accommodation is office guest house"""
        return self.type == AccommodationType.OFFICE_GUEST_HOUSE
    
    @property
    def accommodation_summary(self) -> str:
        """Get human-readable accommodation summary"""
        if self.type == AccommodationType.OFFICE_GUEST_HOUSE:
            bed_info = f" (Bed {self.bed_assigned})" if self.bed_assigned else ""
            return f"Office Guest House{bed_info}"
        elif self.type == AccommodationType.HOTEL:
            return f"Hotel: {self.details}" if self.details else "Hotel"
        else:
            return "Self-arranged"


class Transport(Base):
    """
    Visit Transport Management
    
    Handles pickup, drop, and tour logistics for customer visits.
    """
    __tablename__ = "transports"
    
    # Core transport information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, index=True)
    type = Column(SQLEnum(TransportType), nullable=False, index=True)
    mode = Column(SQLEnum(TransportMode), nullable=False, index=True)
    
    # Transport details
    driver_details = Column(String(200), nullable=True, comment="Driver name, contact, vehicle details")
    time = Column(DateTime, nullable=False, comment="Scheduled pickup/drop time")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    visit = relationship("Visit", back_populates="transports")
    
    def __repr__(self):
        return f"<Transport(id={self.id}, type='{self.type.value}', mode='{self.mode.value}')>"
    
    @property
    def transport_summary(self) -> str:
        """Get human-readable transport summary"""
        type_name = self.type.value.replace('_', ' ').title()
        mode_name = self.mode.value.replace('_', ' ').title()
        time_str = self.time.strftime('%Y-%m-%d %H:%M') if self.time else 'TBD'
        return f"{type_name} via {mode_name} at {time_str}"


class ItineraryItem(Base):
    """
    Visit Itinerary Management
    
    Manages supplier appointments and meeting schedules during customer visits.
    """
    __tablename__ = "itinerary_items"
    
    # Core itinerary information
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False, index=True)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("partners.id"), nullable=False, index=True)
    
    # Appointment details
    appointment_time = Column(DateTime, nullable=False, index=True, comment="Scheduled appointment time")
    status = Column(SQLEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.PENDING, index=True)
    notes = Column(Text, nullable=True, comment="Meeting notes, purpose, special requirements")
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    visit = relationship("Visit", back_populates="itinerary_items")
    supplier = relationship("Partner", foreign_keys=[supplier_id], backref="customer_appointments")
    
    def __repr__(self):
        supplier_name = self.supplier.name if self.supplier else 'Unknown'
        return f"<ItineraryItem(id={self.id}, supplier='{supplier_name}', status='{self.status.value}')>"
    
    @property
    def appointment_summary(self) -> str:
        """Get human-readable appointment summary"""
        supplier_name = self.supplier.name if self.supplier else 'Unknown Supplier'
        time_str = self.appointment_time.strftime('%Y-%m-%d %H:%M') if self.appointment_time else 'TBD'
        status_str = self.status.value.title()
        return f"{time_str} - {supplier_name} ({status_str})"
    
    @property
    def is_confirmed(self) -> bool:
        """Check if appointment is confirmed"""
        return self.status == AppointmentStatus.CONFIRMED
    
    @property
    def is_pending(self) -> bool:
        """Check if appointment is pending confirmation"""
        return self.status == AppointmentStatus.PENDING