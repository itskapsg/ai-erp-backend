"""
Project Namaste - Customer Visit Management API

This module provides REST API endpoints for managing customer visits,
accommodation, transport, supplier itineraries, and meal planning.

Endpoints:
- POST /api/v1/namaste/: Create Visit
- GET /api/v1/namaste/: List visits (Filter by 'Upcoming' or 'Ongoing')
- POST /api/v1/namaste/{id}/itinerary/: Add Supplier Appointment
- GET /api/v1/namaste/{id}/: Get visit details
- POST /api/v1/namaste/{id}/accommodation/: Add accommodation
- POST /api/v1/namaste/{id}/transport/: Add transport
- POST /api/v1/namaste/{id}/meal-plan/: Add meal plan
"""

from datetime import datetime
from datetime import date as date_type
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.core import User
from app.models.namaste import (
    VisitMode, AccommodationType, TransportType, TransportMode, ItineraryStatus,
    DietType, MealLocation
)
from app.services.namaste_service import NamasteService
from app.api.auth import get_current_user

router = APIRouter()


# Pydantic models for request/response
class CreateVisitRequest(BaseModel):
    customer_id: str = Field(..., description="UUID of the customer")
    start_date: datetime = Field(..., description="Visit start date and time")
    end_date: datetime = Field(..., description="Visit end date and time")
    salesperson_id: Optional[str] = Field(None, description="UUID of assigned salesperson")
    visit_mode: VisitMode = Field(VisitMode.ACCOMPANIED, description="Visit mode")
    arrival_details: Optional[str] = Field(None, description="Flight/train details")
    ticket_url: Optional[str] = Field(None, description="URL to ticket confirmation")
    accommodation_type: Optional[AccommodationType] = Field(AccommodationType.NONE, description="Accommodation type")
    accommodation_details: Optional[str] = Field(None, description="Hotel name or details")
    preferred_bed: Optional[int] = Field(None, description="Preferred bed (1-5) for guest house")


class AddAccommodationRequest(BaseModel):
    type: AccommodationType = Field(..., description="Accommodation type")
    details: Optional[str] = Field(None, description="Hotel name, address, or details")
    preferred_bed: Optional[int] = Field(None, description="Preferred bed number (1-5) for guest house")


class AddTransportRequest(BaseModel):
    transport_type: TransportType = Field(..., description="Transport type")
    transport_mode: TransportMode = Field(..., description="Transport mode")
    scheduled_time: datetime = Field(..., description="Scheduled transport time")
    driver_details: Optional[str] = Field(None, description="Driver details")


class AddAppointmentRequest(BaseModel):
    supplier_id: str = Field(..., description="UUID of the supplier")
    appointment_time: datetime = Field(..., description="Scheduled appointment time")
    notes: Optional[str] = Field(None, description="Meeting notes or purpose")
    auto_confirm: bool = Field(False, description="Auto-confirm the appointment")


class AddMealPlanRequest(BaseModel):
    date: date_type = Field(..., description="Date for the meal plan")
    diet: DietType = Field(DietType.STANDARD, description="Dietary preference")
    breakfast: bool = Field(False, description="Include breakfast")
    lunch: MealLocation = Field(MealLocation.OFFICE, description="Lunch location")
    dinner: MealLocation = Field(MealLocation.RESTAURANT, description="Dinner location")
    special_notes: Optional[str] = Field(None, description="Special dietary requirements or notes")


class VisitResponse(BaseModel):
    id: str
    customer_id: str
    customer_name: str
    salesperson_id: Optional[str]
    salesperson_name: Optional[str]
    start_date: datetime
    end_date: datetime
    status: str
    visit_mode: str
    arrival_details: Optional[str]
    ticket_url: Optional[str]
    duration_days: int


class BedAvailabilityResponse(BaseModel):
    date: date_type
    total_beds: int
    available_beds: List[int]
    occupied_beds: List[int]
    available_count: int
    occupied_count: int
    is_fully_booked: bool
    occupancy_details: List[Dict[str, Any]]


@router.post("/", response_model=Dict[str, Any])
async def create_visit(
    request: CreateVisitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new customer visit
    
    Creates a visit record with the specified details. The visit will be in SCHEDULED status.
    """
    try:
        namaste_service = NamasteService(db)
        
        visit = namaste_service.create_visit(
            customer_id=request.customer_id,
            start_date=request.start_date,
            end_date=request.end_date,
            salesperson_id=request.salesperson_id,
            visit_mode=request.visit_mode,
            arrival_details=request.arrival_details,
            ticket_url=request.ticket_url,
            accommodation_type=request.accommodation_type,
            accommodation_details=request.accommodation_details,
            preferred_bed=request.preferred_bed,
            user=current_user
        )
        
        db.commit()
        
        # Return visit summary
        return namaste_service.get_visit_summary(str(visit.id))
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create visit: {str(e)}")


@router.get("/", response_model=List[Dict[str, Any]])
async def list_visits(
    filter_type: Optional[str] = Query(None, description="Filter: 'upcoming', 'ongoing', or None for all"),
    days_ahead: int = Query(30, description="Days ahead to look for upcoming visits"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List visits with optional filtering
    
    Supports filtering by:
    - 'upcoming': Visits scheduled within the next N days
    - 'ongoing': Currently active visits
    - None: All visits
    """
    try:
        namaste_service = NamasteService(db)
        
        if filter_type == "upcoming":
            visits = namaste_service.get_upcoming_visits(days_ahead=days_ahead)
        elif filter_type == "ongoing":
            # Get ongoing visits (you can implement this method in the service)
            visits = namaste_service.get_upcoming_visits(days_ahead=0)
            visits = [v for v in visits if v['visit']['status'] == 'ongoing']
        else:
            # Get all recent visits (last 90 days + next 30 days)
            visits = namaste_service.get_upcoming_visits(days_ahead=30)
        
        return visits
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list visits: {str(e)}")


@router.get("/{visit_id}", response_model=Dict[str, Any])
async def get_visit_details(
    visit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific visit
    
    Returns complete visit information including accommodation, transport, and itinerary.
    """
    try:
        namaste_service = NamasteService(db)
        return namaste_service.get_visit_summary(visit_id)
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get visit details: {str(e)}")


@router.post("/{visit_id}/accommodation/", response_model=Dict[str, Any])
async def add_accommodation(
    visit_id: str,
    request: AddAccommodationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add accommodation to a visit
    
    For guest house accommodation, automatically assigns an available bed.
    """
    try:
        namaste_service = NamasteService(db)
        
        if request.type == AccommodationType.OFFICE_GUEST_HOUSE:
            # Use the service method for guest house bed assignment
            accommodation = namaste_service.assign_guest_house_bed(
                visit_id=visit_id,
                preferred_bed=request.preferred_bed
            )
        else:
            # For hotel or self accommodation, create directly
            from app.models.namaste import Accommodation
            accommodation = Accommodation(
                visit_id=visit_id,
                type=request.type,
                details=request.details
            )
            db.add(accommodation)
            db.flush()
        
        db.commit()
        
        # Return updated visit summary
        return namaste_service.get_visit_summary(visit_id)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add accommodation: {str(e)}")


@router.post("/{visit_id}/transport/", response_model=Dict[str, Any])
async def add_transport(
    visit_id: str,
    request: AddTransportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add transport arrangement to a visit
    
    Creates transport logistics for pickup, drop, or market tours.
    """
    try:
        namaste_service = NamasteService(db)
        
        transport = namaste_service.add_transport(
            visit_id=visit_id,
            transport_type=request.transport_type,
            transport_mode=request.transport_mode,
            scheduled_time=request.scheduled_time,
            driver_details=request.driver_details
        )
        
        db.commit()
        
        # Return updated visit summary
        return namaste_service.get_visit_summary(visit_id)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add transport: {str(e)}")


@router.post("/{visit_id}/itinerary/", response_model=Dict[str, Any])
async def add_appointment(
    visit_id: str,
    request: AddAppointmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add supplier appointment to visit itinerary
    
    Creates an appointment with a supplier and sends notification alert.
    """
    try:
        namaste_service = NamasteService(db)
        
        itinerary_item = namaste_service.add_appointment(
            visit_id=visit_id,
            supplier_id=request.supplier_id,
            appointment_time=request.appointment_time,
            notes=request.notes,
            auto_confirm=request.auto_confirm
        )
        
        db.commit()
        
        # Return updated visit summary
        return namaste_service.get_visit_summary(visit_id)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add appointment: {str(e)}")


@router.get("/beds/availability", response_model=BedAvailabilityResponse)
async def check_bed_availability(
    check_date: date_type = Query(..., description="Date to check bed availability"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check guest house bed availability for a specific date
    
    Returns which of the 5 beds are available or occupied.
    """
    try:
        namaste_service = NamasteService(db)
        availability = namaste_service.check_bed_availability(check_date)
        
        return BedAvailabilityResponse(**availability)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check bed availability: {str(e)}")


@router.get("/reports/occupancy", response_model=Dict[str, Any])
async def get_occupancy_report(
    start_date: date_type = Query(..., description="Report start date"),
    end_date: date_type = Query(..., description="Report end date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get guest house occupancy report for a date range
    
    Returns detailed occupancy statistics and daily breakdown.
    """
    try:
        namaste_service = NamasteService(db)
        report = namaste_service.get_guest_house_occupancy_report(start_date, end_date)
        
        return report
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate occupancy report: {str(e)}")


@router.post("/{visit_id}/meal-plan", response_model=Dict[str, Any])
async def add_meal_plan(
    visit_id: str,
    request: AddMealPlanRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add or update meal plan for a visit
    
    Creates a meal plan for a specific date. If a plan already exists for that date,
    it will be updated. Generates alerts for office lunch orders and special dietary requirements.
    """
    try:
        meal_plan = NamasteService.add_meal_plan(db, visit_id, request)
        
        return {
            "success": True,
            "message": "Meal plan added successfully",
            "meal_plan": {
                "id": str(meal_plan.id),
                "visit_id": str(meal_plan.visit_id),
                "date": meal_plan.date.isoformat(),
                "diet": meal_plan.diet,
                "breakfast": meal_plan.breakfast,
                "lunch": meal_plan.lunch,
                "dinner": meal_plan.dinner,
                "special_notes": meal_plan.special_notes
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to add meal plan: {str(e)}")