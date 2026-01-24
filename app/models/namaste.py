import enum
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, Boolean, Text, Enum, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.core import Base
import uuid
from datetime import datetime

class VisitStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    ONGOING = "ONGOING"
    COMPLETED = "COMPLETED"

class VisitMode(str, enum.Enum):
    ACCOMPANIED = "ACCOMPANIED"
    SOLO = "SOLO"
    MIXED = "MIXED"

class AccommodationType(str, enum.Enum):
    OFFICE_GUEST_HOUSE = "OFFICE_GUEST_HOUSE"
    HOTEL = "HOTEL"
    SELF = "SELF"

class TransportType(str, enum.Enum):
    PICKUP = "PICKUP"
    DROP = "DROP"
    MARKET_TOUR = "MARKET_TOUR"

class TransportMode(str, enum.Enum):
    COMPANY_DRIVER = "COMPANY_DRIVER"
    TAXI = "TAXI"
    AUTO = "AUTO"
    SELF = "SELF"

class ItineraryStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    COMPLETED = "COMPLETED"

# --- NEW FOOD ENUMS ---
class DietType(str, enum.Enum):
    STANDARD = "STANDARD"
    JAIN = "JAIN"
    VEG_ONLY = "VEG_ONLY"
    VEGAN = "VEGAN"

class MealLocation(str, enum.Enum):
    OFFICE = "OFFICE"
    RESTAURANT = "RESTAURANT"
    SUPPLIER = "SUPPLIER"
    SKIP = "SKIP"

class Visit(Base):
    __tablename__ = "visits"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, ForeignKey("partners.id"), nullable=False)
    salesperson_id = Column(String, ForeignKey("users.id"), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    status = Column(Enum(VisitStatus), default=VisitStatus.SCHEDULED)
    visit_mode = Column(Enum(VisitMode), default=VisitMode.ACCOMPANIED)
    arrival_details = Column(Text, nullable=True)
    ticket_url = Column(String, nullable=True)
    
    accommodations = relationship("Accommodation", back_populates="visit")
    transports = relationship("Transport", back_populates="visit")
    itinerary_items = relationship("ItineraryItem", back_populates="visit")
    meal_plans = relationship("MealPlan", back_populates="visit")

class Accommodation(Base):
    __tablename__ = "accommodations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id = Column(String, ForeignKey("visits.id"), nullable=False)
    type = Column(Enum(AccommodationType), nullable=False)
    details = Column(Text, nullable=True)
    bed_assigned = Column(Integer, nullable=True)
    
    visit = relationship("Visit", back_populates="accommodations")

class Transport(Base):
    __tablename__ = "transports"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id = Column(String, ForeignKey("visits.id"), nullable=False)
    type = Column(Enum(TransportType), nullable=False)
    mode = Column(Enum(TransportMode), nullable=False)
    driver_details = Column(String, nullable=True)
    time = Column(DateTime, nullable=False)
    
    visit = relationship("Visit", back_populates="transports")

class ItineraryItem(Base):
    __tablename__ = "itinerary_items"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    visit_id = Column(String, ForeignKey("visits.id"), nullable=False)
    supplier_id = Column(String, ForeignKey("partners.id"), nullable=False)
    appointment_time = Column(DateTime, nullable=False)
    status = Column(Enum(ItineraryStatus), default=ItineraryStatus.PENDING)
    notes = Column(Text, nullable=True)
    
    visit = relationship("Visit", back_populates="itinerary_items")

# --- NEW MEAL PLAN MODEL ---
class MealPlan(Base):
    __tablename__ = "meal_plans"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    visit_id = Column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False)
    date = Column(Date, nullable=False)
    diet = Column(Enum(DietType), default=DietType.STANDARD)
    breakfast = Column(Boolean, default=False)
    lunch = Column(Enum(MealLocation), default=MealLocation.OFFICE)
    dinner = Column(Enum(MealLocation), default=MealLocation.RESTAURANT)
    special_notes = Column(Text, nullable=True)
    
    visit = relationship("Visit", back_populates="meal_plans")