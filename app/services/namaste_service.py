"""
Project Namaste - Customer Visit Management Service

This service handles Customer Arrivals, Accommodation (Guest House/Hotel), 
Logistics, and Supplier Itineraries for business visits.

Key Features:
- Visit creation and management
- Guest house bed availability checking (5 beds total)
- Transport logistics coordination
- Supplier appointment scheduling with alerts
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.namaste import (
    Visit, VisitStatus, VisitMode,
    Accommodation, AccommodationType,
    Transport, TransportType, TransportMode,
    ItineraryItem, ItineraryStatus,
    MealPlan, DietType, MealLocation
)
from app.models.masters import Partner, PartnerType
from app.models.core import User

logger = logging.getLogger(__name__)


class NamasteService:
    """
    Project Namaste - Customer Visit Management Service
    
    Handles all aspects of customer visit management including accommodation,
    transport, and supplier itinerary coordination.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def create_visit(
        self,
        customer_id: str,
        start_date: datetime,
        end_date: datetime,
        salesperson_id: Optional[str] = None,
        visit_mode: VisitMode = VisitMode.ACCOMPANIED,
        arrival_details: Optional[str] = None,
        ticket_url: Optional[str] = None,
        user: Optional[User] = None
    ) -> Visit:
        """
        Create a new customer visit
        
        Args:
            customer_id: UUID of the customer (Partner)
            start_date: Visit start date and time
            end_date: Visit end date and time
            salesperson_id: Optional UUID of assigned salesperson
            visit_mode: ACCOMPANIED or SOLO
            arrival_details: Flight/train details
            ticket_url: URL to ticket confirmation
            user: User creating the visit
            
        Returns:
            Visit: Created visit object
        """
        # Validate customer exists and is a customer
        customer = self.db.query(Partner).filter_by(id=customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID {customer_id} not found")
        
        if customer.type != PartnerType.CUSTOMER:
            raise ValueError(f"Partner {customer.name} is not a customer")
        
        # Validate salesperson if provided
        if salesperson_id:
            salesperson = self.db.query(User).filter_by(id=salesperson_id).first()
            if not salesperson:
                raise ValueError(f"Salesperson with ID {salesperson_id} not found")
        
        # Validate dates
        if start_date >= end_date:
            raise ValueError("Start date must be before end date")
        
        # Create visit
        visit = Visit(
            customer_id=customer_id,
            salesperson_id=salesperson_id,
            start_date=start_date,
            end_date=end_date,
            visit_mode=visit_mode,
            arrival_details=arrival_details,
            ticket_url=ticket_url,
            status=VisitStatus.SCHEDULED
        )
        
        self.db.add(visit)
        self.db.flush()  # Get the ID
        
        logger.info(f"📅 Visit created for {customer.name} from {start_date.date()} to {end_date.date()}")
        
        return visit
    
    def check_bed_availability(self, check_date: date) -> Dict[str, Any]:
        """
        Check which of the 5 guest house beds are available on a given date
        
        Args:
            check_date: Date to check availability for
            
        Returns:
            Dict with availability information
        """
        # Query all accommodations that overlap with the check date
        # Convert check_date to datetime for comparison
        from datetime import datetime, time
        check_datetime_start = datetime.combine(check_date, time.min)
        check_datetime_end = datetime.combine(check_date, time.max)
        
        overlapping_accommodations = self.db.query(Accommodation).join(Visit).filter(
            and_(
                Accommodation.type == AccommodationType.OFFICE_GUEST_HOUSE,
                Accommodation.bed_assigned.isnot(None),
                Visit.start_date <= check_datetime_end,
                Visit.end_date >= check_datetime_start,
                Visit.status.in_([VisitStatus.SCHEDULED, VisitStatus.ONGOING])
            )
        ).all()
        
        # Track occupied beds
        occupied_beds = set()
        occupancy_details = []
        
        for accommodation in overlapping_accommodations:
            if accommodation.bed_assigned:
                occupied_beds.add(accommodation.bed_assigned)
                occupancy_details.append({
                    'bed': accommodation.bed_assigned,
                    'customer': accommodation.visit.customer.name,
                    'visit_id': str(accommodation.visit.id),
                    'start_date': accommodation.visit.start_date.date(),
                    'end_date': accommodation.visit.end_date.date()
                })
        
        # Determine available beds (1-5)
        all_beds = set(range(1, 6))  # Beds 1, 2, 3, 4, 5
        available_beds = sorted(list(all_beds - occupied_beds))
        occupied_beds_list = sorted(list(occupied_beds))
        
        availability_info = {
            'date': check_date,
            'total_beds': 5,
            'available_beds': available_beds,
            'occupied_beds': occupied_beds_list,
            'available_count': len(available_beds),
            'occupied_count': len(occupied_beds),
            'occupancy_details': occupancy_details,
            'is_fully_booked': len(available_beds) == 0
        }
        
        logger.info(f"🛏️  Bed availability for {check_date}: {len(available_beds)}/5 beds available")
        
        return availability_info
    
    def assign_guest_house_bed(self, visit_id: str, preferred_bed: Optional[int] = None) -> Accommodation:
        """
        Assign a guest house bed to a visit
        
        Args:
            visit_id: UUID of the visit
            preferred_bed: Preferred bed number (1-5), if available
            
        Returns:
            Accommodation: Created accommodation object
        """
        visit = self.db.query(Visit).filter_by(id=visit_id).first()
        if not visit:
            raise ValueError(f"Visit with ID {visit_id} not found")
        
        # Check if visit already has guest house accommodation
        existing_accommodation = self.db.query(Accommodation).filter_by(
            visit_id=visit_id,
            type=AccommodationType.OFFICE_GUEST_HOUSE
        ).first()
        
        if existing_accommodation:
            raise ValueError(f"Visit already has guest house accommodation (Bed {existing_accommodation.bed_assigned})")
        
        # Check bed availability for the visit duration
        availability = self.check_bed_availability(visit.start_date.date())
        
        if availability['is_fully_booked']:
            raise ValueError(f"Guest house is fully booked for {visit.start_date.date()}")
        
        # Determine bed to assign
        bed_to_assign = None
        
        if preferred_bed and preferred_bed in availability['available_beds']:
            bed_to_assign = preferred_bed
        else:
            # Assign the lowest available bed number
            bed_to_assign = min(availability['available_beds'])
        
        # Create accommodation
        accommodation = Accommodation(
            visit_id=visit_id,
            type=AccommodationType.OFFICE_GUEST_HOUSE,
            bed_assigned=bed_to_assign,
            details=f"Office Guest House - Bed {bed_to_assign}"
        )
        
        self.db.add(accommodation)
        self.db.flush()
        
        logger.info(f"🛏️  Assigned Bed {bed_to_assign} to {visit.customer.name} for visit {visit_id}")
        
        return accommodation
    
    def add_transport(
        self,
        visit_id: str,
        transport_type: TransportType,
        transport_mode: TransportMode,
        scheduled_time: datetime,
        driver_details: Optional[str] = None
    ) -> Transport:
        """
        Add transport arrangement to a visit
        
        Args:
            visit_id: UUID of the visit
            transport_type: PICKUP, DROP, or MARKET_TOUR
            transport_mode: COMPANY_DRIVER, TAXI, AUTO, or SELF
            scheduled_time: When the transport is scheduled
            driver_details: Driver name, contact, vehicle details
            
        Returns:
            Transport: Created transport object
        """
        visit = self.db.query(Visit).filter_by(id=visit_id).first()
        if not visit:
            raise ValueError(f"Visit with ID {visit_id} not found")
        
        # Create transport
        transport = Transport(
            visit_id=visit_id,
            type=transport_type,
            mode=transport_mode,
            time=scheduled_time,
            driver_details=driver_details
        )
        
        self.db.add(transport)
        self.db.flush()
        
        logger.info(f"🚗 Transport added: {transport_type.value} via {transport_mode.value} for {visit.customer.name}")
        
        return transport
    
    def add_appointment(
        self,
        visit_id: str,
        supplier_id: str,
        appointment_time: datetime,
        notes: Optional[str] = None,
        auto_confirm: bool = False
    ) -> ItineraryItem:
        """
        Add supplier appointment to visit itinerary
        
        Args:
            visit_id: UUID of the visit
            supplier_id: UUID of the supplier (Partner)
            appointment_time: Scheduled appointment time
            notes: Meeting notes, purpose, special requirements
            auto_confirm: Whether to auto-confirm the appointment
            
        Returns:
            ItineraryItem: Created itinerary item
        """
        # Validate visit exists
        visit = self.db.query(Visit).filter_by(id=visit_id).first()
        if not visit:
            raise ValueError(f"Visit with ID {visit_id} not found")
        
        # Validate supplier exists and is a supplier
        supplier = self.db.query(Partner).filter_by(id=supplier_id).first()
        if not supplier:
            raise ValueError(f"Supplier with ID {supplier_id} not found")
        
        if supplier.type != PartnerType.SUPPLIER:
            raise ValueError(f"Partner {supplier.name} is not a supplier")
        
        # Create itinerary item
        status = AppointmentStatus.CONFIRMED if auto_confirm else AppointmentStatus.PENDING
        
        itinerary_item = ItineraryItem(
            visit_id=visit_id,
            supplier_id=supplier_id,
            appointment_time=appointment_time,
            status=status,
            notes=notes
        )
        
        self.db.add(itinerary_item)
        self.db.flush()
        
        # Log alert for supplier notification
        time_str = appointment_time.strftime('%Y-%m-%d %H:%M')
        customer_name = visit.customer.name
        
        print(f"📢 ALERT: Notify Supplier [{supplier.name}] about visit at [{time_str}]")
        print(f"   Customer: {customer_name}")
        print(f"   Status: {status.value.upper()}")
        if notes:
            print(f"   Notes: {notes}")
        
        logger.info(f"📅 Appointment added: {supplier.name} at {time_str} for {customer_name}")
        
        return itinerary_item
    
    def add_meal_plan(
        self,
        visit_id: str,
        date: date,
        diet: DietType = DietType.STANDARD,
        breakfast: bool = False,
        lunch: MealLocation = MealLocation.OFFICE,
        dinner: MealLocation = MealLocation.RESTAURANT,
        special_notes: Optional[str] = None
    ) -> MealPlan:
        """
        Add meal plan for a specific date during the visit
        
        Args:
            visit_id: Visit ID
            date: Date for meal plan
            diet: Dietary preference
            breakfast: Whether breakfast arrangement is needed
            lunch: Lunch location
            dinner: Dinner location
            special_notes: Special dietary requirements
            
        Returns:
            Created MealPlan instance
            
        Raises:
            ValueError: If visit not found or date is outside visit period
        """
        # Validate visit exists
        visit = self.db.query(Visit).filter(Visit.id == visit_id).first()
        if not visit:
            raise ValueError(f"Visit with ID {visit_id} not found")
        
        # Validate date is within visit period
        visit_start_date = visit.start_date.date()
        visit_end_date = visit.end_date.date()
        
        if date < visit_start_date or date > visit_end_date:
            raise ValueError(f"Meal plan date {date} is outside visit period ({visit_start_date} to {visit_end_date})")
        
        # Check if meal plan already exists for this date
        existing_plan = self.db.query(MealPlan).filter(
            and_(
                MealPlan.visit_id == visit_id,
                MealPlan.date == date
            )
        ).first()
        
        if existing_plan:
            raise ValueError(f"Meal plan already exists for {date}")
        
        # Create meal plan
        meal_plan = MealPlan(
            visit_id=visit_id,
            date=date,
            diet=diet,
            breakfast=breakfast,
            lunch=lunch,
            dinner=dinner,
            special_notes=special_notes
        )
        
        self.db.add(meal_plan)
        self.db.commit()
        self.db.refresh(meal_plan)
        
        # Generate alerts for office arrangements
        if meal_plan.needs_office_lunch:
            print(f"🍱 Tiffin Alert: Order {diet.value.upper()} lunch for {date}")
        
        if meal_plan.needs_breakfast:
            print(f"🥐 Breakfast Alert: Arrange {diet.value.upper()} breakfast for {date}")
        
        # Log special requirements
        if meal_plan.has_special_requirements:
            print(f"⚠️  Special Diet Alert: {special_notes} for {date}")
        
        logger.info(f"Meal plan created for visit {visit_id} on {date}")
        
        return meal_plan
    
    @staticmethod
    def add_meal_plan(db, visit_id, meal_data):
        # Check for existing plan for this date
        existing = db.query(MealPlan).filter_by(visit_id=visit_id, date=meal_data.date).first()
        if existing:
            # Update existing
            for key, value in meal_data.dict(exclude_unset=True).items():
                setattr(existing, key, value)
            db.commit()
            db.refresh(existing)
            return existing
        
        # Create new
        plan = MealPlan(visit_id=visit_id, **meal_data.dict())
        db.add(plan)
        db.commit()
        db.refresh(plan)
        
        # ALERT LOGIC
        if plan.lunch == MealLocation.OFFICE:
            print(f"🍱 Tiffin Alert: Order {plan.diet} lunch for {plan.date} (Visit {visit_id})")
            
        return plan
    
    def get_visit_summary(self, visit_id: str) -> Dict[str, Any]:
        """
        Get comprehensive visit summary including all details
        
        Args:
            visit_id: UUID of the visit
            
        Returns:
            Dict with complete visit information
        """
        visit = self.db.query(Visit).filter_by(id=visit_id).first()
        if not visit:
            raise ValueError(f"Visit with ID {visit_id} not found")
        
        # Get accommodations
        accommodations = []
        for acc in visit.accommodations:
            accommodations.append({
                'id': str(acc.id),
                'type': acc.type.value,
                'details': acc.details,
                'bed_assigned': acc.bed_assigned,
                'summary': acc.accommodation_summary
            })
        
        # Get transports
        transports = []
        for transport in visit.transports:
            transports.append({
                'id': str(transport.id),
                'type': transport.type.value,
                'mode': transport.mode.value,
                'time': transport.time.isoformat() if transport.time else None,
                'driver_details': transport.driver_details,
                'summary': transport.transport_summary
            })
        
        # Get itinerary
        itinerary = []
        for item in visit.itinerary_items:
            itinerary.append({
                'id': str(item.id),
                'supplier_id': str(item.supplier_id),
                'supplier_name': item.supplier.name,
                'appointment_time': item.appointment_time.isoformat() if item.appointment_time else None,
                'status': item.status.value,
                'notes': item.notes,
                'summary': item.appointment_summary
            })
        
        return {
            'visit': {
                'id': str(visit.id),
                'customer_id': str(visit.customer_id),
                'customer_name': visit.customer.name,
                'salesperson_id': str(visit.salesperson_id) if visit.salesperson_id else None,
                'salesperson_name': visit.salesperson.username if visit.salesperson else None,
                'start_date': visit.start_date.isoformat(),
                'end_date': visit.end_date.isoformat(),
                'status': visit.status.value,
                'visit_mode': visit.visit_mode.value,
                'arrival_details': visit.arrival_details,
                'ticket_url': visit.ticket_url,
                'duration_days': visit.duration_days
            },
            'accommodations': accommodations,
            'transports': transports,
            'itinerary': itinerary,
            'summary': {
                'has_accommodation': visit.has_accommodation,
                'has_transport': visit.has_transport,
                'total_appointments': len(itinerary),
                'confirmed_appointments': len([i for i in itinerary if i['status'] == 'confirmed'])
            }
        }
    
    def get_upcoming_visits(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """
        Get upcoming visits within specified days
        
        Args:
            days_ahead: Number of days to look ahead
            
        Returns:
            List of visit summaries
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        
        upcoming_visits = self.db.query(Visit).filter(
            and_(
                Visit.start_date <= cutoff_date,
                Visit.status.in_([VisitStatus.SCHEDULED, VisitStatus.ONGOING])
            )
        ).order_by(Visit.start_date).all()
        
        visit_summaries = []
        for visit in upcoming_visits:
            summary = self.get_visit_summary(str(visit.id))
            visit_summaries.append(summary)
        
        return visit_summaries
    
    def get_guest_house_occupancy_report(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Get guest house occupancy report for a date range
        
        Args:
            start_date: Report start date
            end_date: Report end date
            
        Returns:
            Dict with occupancy statistics
        """
        from datetime import timedelta
        
        daily_occupancy = []
        current_date = start_date
        
        while current_date <= end_date:
            availability = self.check_bed_availability(current_date)
            daily_occupancy.append({
                'date': current_date,
                'occupied_beds': availability['occupied_count'],
                'available_beds': availability['available_count'],
                'occupancy_rate': (availability['occupied_count'] / 5) * 100,
                'is_fully_booked': availability['is_fully_booked'],
                'occupancy_details': availability['occupancy_details']
            })
            current_date += timedelta(days=1)
        
        # Calculate summary statistics
        total_days = len(daily_occupancy)
        total_bed_days = total_days * 5
        occupied_bed_days = sum(day['occupied_beds'] for day in daily_occupancy)
        average_occupancy = (occupied_bed_days / total_bed_days) * 100 if total_bed_days > 0 else 0
        fully_booked_days = len([day for day in daily_occupancy if day['is_fully_booked']])
        
        return {
            'period': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'statistics': {
                'total_bed_days': total_bed_days,
                'occupied_bed_days': occupied_bed_days,
                'average_occupancy_rate': round(average_occupancy, 2),
                'fully_booked_days': fully_booked_days,
                'peak_occupancy': max(day['occupied_beds'] for day in daily_occupancy) if daily_occupancy else 0
            },
            'daily_occupancy': daily_occupancy
        }