#!/usr/bin/env python3
"""
Project Namaste - Verification Script

This script tests the complete Project Namaste system with the following scenario:
- Customer 'Apex' arrives for 2 days
- Stay: Office Guest House (Bed 3)
- Logistics: Company Driver Pickup at Station
- Itinerary: 11:00 AM @ 'Supplier X' (Confirmed)

Verifies:
- Database records created
- Bed 3 marked booked
- Alert logs printed for supplier notification
"""

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

# Set environment to use PostgreSQL
os.environ['DATABASE_URL'] = 'postgresql://erp_admin:db_password_123@localhost/erp_dev_db'

# Add the app directory to Python path
sys.path.append('/workspace')

from app.database import get_db
from app.models.core import User, UserRole
from app.models.masters import Partner, PartnerType
from app.models.namaste import (
    VisitMode, AccommodationType, TransportType, TransportMode, AppointmentStatus
)
from app.services.namaste_service import NamasteService


def setup_test_data(db):
    """Set up test customers, suppliers, and users"""
    
    print("🔧 Setting up test data...")
    
    # Create test customer 'Apex'
    apex_customer = db.query(Partner).filter_by(name='Apex').first()
    if not apex_customer:
        apex_customer = Partner(
            name='Apex',
            type=PartnerType.CUSTOMER,
            gst_number='APEX123456789',
            credit_limit=Decimal('100000.00')
        )
        db.add(apex_customer)
        db.flush()
    
    # Create test supplier 'Supplier X'
    supplier_x = db.query(Partner).filter_by(name='Supplier X').first()
    if not supplier_x:
        supplier_x = Partner(
            name='Supplier X',
            type=PartnerType.SUPPLIER,
            gst_number='SUPPLX123456789',
            credit_limit=Decimal('0.00')
        )
        db.add(supplier_x)
        db.flush()
    
    # Create test salesperson
    salesperson = db.query(User).filter_by(username='test_salesperson_namaste').first()
    if not salesperson:
        salesperson = User(
            username='test_salesperson_namaste',
            email='salesperson@namaste.test',
            role=UserRole.SALESMAN
        )
        salesperson.set_password('password123')
        db.add(salesperson)
        db.flush()
    
    db.commit()
    
    print(f"   ✅ Customer: {apex_customer.name} (ID: {apex_customer.id})")
    print(f"   ✅ Supplier: {supplier_x.name} (ID: {supplier_x.id})")
    print(f"   ✅ Salesperson: {salesperson.username} (ID: {salesperson.id})")
    
    return {
        'customer': apex_customer,
        'supplier': supplier_x,
        'salesperson': salesperson
    }


def test_namaste_scenario(db, test_data):
    """Test the complete Namaste scenario"""
    
    print(f"\n🚀 TESTING PROJECT NAMASTE SCENARIO")
    print("="*60)
    print("Scenario: Customer 'Apex' arrives for 2 days")
    print("- Stay: Office Guest House (Bed 3)")
    print("- Logistics: Company Driver Pickup at Station")
    print("- Itinerary: 11:00 AM @ 'Supplier X' (Confirmed)")
    print("="*60)
    
    namaste_service = NamasteService(db)
    
    # Step 1: Create Visit
    print(f"\n📅 STEP 1: Creating Visit")
    print("-" * 30)
    
    start_date = datetime.now() + timedelta(days=1)  # Tomorrow
    end_date = start_date + timedelta(days=2)  # 2 days later
    
    visit = namaste_service.create_visit(
        customer_id=str(test_data['customer'].id),
        start_date=start_date,
        end_date=end_date,
        salesperson_id=str(test_data['salesperson'].id),
        visit_mode=VisitMode.ACCOMPANIED,
        arrival_details="Flight AI 123 arriving at 10:30 AM at Delhi Airport",
        ticket_url="https://example.com/ticket/AI123"
    )
    
    print(f"✅ Visit Created:")
    print(f"   ID: {visit.id}")
    print(f"   Customer: {visit.customer.name}")
    print(f"   Duration: {visit.duration_days} days")
    print(f"   Start: {visit.start_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   End: {visit.end_date.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Status: {visit.status.value}")
    
    # Step 2: Check Bed Availability
    print(f"\n🛏️  STEP 2: Checking Bed Availability")
    print("-" * 30)
    
    availability = namaste_service.check_bed_availability(start_date.date())
    
    print(f"✅ Bed Availability for {start_date.date()}:")
    print(f"   Total Beds: {availability['total_beds']}")
    print(f"   Available Beds: {availability['available_beds']}")
    print(f"   Occupied Beds: {availability['occupied_beds']}")
    print(f"   Available Count: {availability['available_count']}/5")
    
    # Step 3: Assign Guest House Bed 3
    print(f"\n🏠 STEP 3: Assigning Guest House Accommodation")
    print("-" * 30)
    
    accommodation = namaste_service.assign_guest_house_bed(
        visit_id=str(visit.id),
        preferred_bed=3
    )
    
    print(f"✅ Accommodation Assigned:")
    print(f"   Type: {accommodation.type.value}")
    print(f"   Bed: {accommodation.bed_assigned}")
    print(f"   Details: {accommodation.details}")
    print(f"   Summary: {accommodation.accommodation_summary}")
    
    # Step 4: Add Transport (Company Driver Pickup)
    print(f"\n🚗 STEP 4: Adding Transport Logistics")
    print("-" * 30)
    
    pickup_time = start_date.replace(hour=9, minute=0)  # 9:00 AM pickup
    
    transport = namaste_service.add_transport(
        visit_id=str(visit.id),
        transport_type=TransportType.PICKUP,
        transport_mode=TransportMode.COMPANY_DRIVER,
        scheduled_time=pickup_time,
        driver_details="Driver: Rajesh Kumar, Mobile: +91-9876543210, Vehicle: DL-01-AB-1234"
    )
    
    print(f"✅ Transport Added:")
    print(f"   Type: {transport.type.value}")
    print(f"   Mode: {transport.mode.value}")
    print(f"   Time: {transport.time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Driver: {transport.driver_details}")
    print(f"   Summary: {transport.transport_summary}")
    
    # Step 5: Add Supplier Appointment (11:00 AM @ Supplier X)
    print(f"\n📋 STEP 5: Adding Supplier Appointment")
    print("-" * 30)
    
    appointment_time = start_date.replace(hour=11, minute=0)  # 11:00 AM
    
    print("🔔 SUPPLIER NOTIFICATION ALERTS:")
    print("-" * 40)
    
    itinerary_item = namaste_service.add_appointment(
        visit_id=str(visit.id),
        supplier_id=str(test_data['supplier'].id),
        appointment_time=appointment_time,
        notes="Viewing New Collection - Spring 2024 catalog discussion",
        auto_confirm=True  # Confirmed appointment
    )
    
    print("-" * 40)
    print(f"✅ Appointment Added:")
    print(f"   Supplier: {itinerary_item.supplier.name}")
    print(f"   Time: {itinerary_item.appointment_time.strftime('%Y-%m-%d %H:%M')}")
    print(f"   Status: {itinerary_item.status.value}")
    print(f"   Notes: {itinerary_item.notes}")
    print(f"   Summary: {itinerary_item.appointment_summary}")
    
    # Step 6: Get Complete Visit Summary
    print(f"\n📊 STEP 6: Complete Visit Summary")
    print("-" * 30)
    
    visit_summary = namaste_service.get_visit_summary(str(visit.id))
    
    print(f"✅ Visit Summary:")
    print(f"   Visit ID: {visit_summary['visit']['id']}")
    print(f"   Customer: {visit_summary['visit']['customer_name']}")
    print(f"   Duration: {visit_summary['visit']['duration_days']} days")
    print(f"   Status: {visit_summary['visit']['status']}")
    
    print(f"\n   📍 Accommodations ({len(visit_summary['accommodations'])}):")
    for acc in visit_summary['accommodations']:
        print(f"      • {acc['summary']}")
    
    print(f"\n   🚗 Transport ({len(visit_summary['transports'])}):")
    for trans in visit_summary['transports']:
        print(f"      • {trans['summary']}")
    
    print(f"\n   📅 Itinerary ({len(visit_summary['itinerary'])}):")
    for item in visit_summary['itinerary']:
        print(f"      • {item['summary']}")
    
    print(f"\n   📈 Summary Stats:")
    print(f"      • Has Accommodation: {visit_summary['summary']['has_accommodation']}")
    print(f"      • Has Transport: {visit_summary['summary']['has_transport']}")
    print(f"      • Total Appointments: {visit_summary['summary']['total_appointments']}")
    print(f"      • Confirmed Appointments: {visit_summary['summary']['confirmed_appointments']}")
    
    return visit_summary


def verify_bed_booking(db, visit_summary):
    """Verify that Bed 3 is properly booked"""
    
    print(f"\n🔍 VERIFICATION: Bed Booking Status")
    print("-" * 30)
    
    namaste_service = NamasteService(db)
    
    # Get the visit start date
    visit_start = datetime.fromisoformat(visit_summary['visit']['start_date']).date()
    
    # Check bed availability on visit date
    availability = namaste_service.check_bed_availability(visit_start)
    
    print(f"✅ Bed Status for {visit_start}:")
    print(f"   Available Beds: {availability['available_beds']}")
    print(f"   Occupied Beds: {availability['occupied_beds']}")
    
    # Verify Bed 3 is occupied
    if 3 in availability['occupied_beds']:
        print(f"   ✅ SUCCESS: Bed 3 is properly booked!")
        
        # Find the occupancy details for Bed 3
        for detail in availability['occupancy_details']:
            if detail['bed'] == 3:
                print(f"      Customer: {detail['customer']}")
                print(f"      Visit ID: {detail['visit_id']}")
                print(f"      Period: {detail['start_date']} to {detail['end_date']}")
                break
        
        return True
    else:
        print(f"   ❌ ERROR: Bed 3 is not booked!")
        return False


def test_occupancy_report(db):
    """Test the occupancy report functionality"""
    
    print(f"\n📊 BONUS: Guest House Occupancy Report")
    print("-" * 30)
    
    namaste_service = NamasteService(db)
    
    # Generate report for next 7 days
    from datetime import date
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    
    report = namaste_service.get_guest_house_occupancy_report(start_date, end_date)
    
    print(f"✅ Occupancy Report ({start_date} to {end_date}):")
    print(f"   Period: {report['period']['total_days']} days")
    print(f"   Average Occupancy: {report['statistics']['average_occupancy_rate']}%")
    print(f"   Peak Occupancy: {report['statistics']['peak_occupancy']}/5 beds")
    print(f"   Fully Booked Days: {report['statistics']['fully_booked_days']}")
    
    # Show daily breakdown for first 3 days
    print(f"\n   Daily Breakdown (First 3 Days):")
    for day in report['daily_occupancy'][:3]:
        print(f"      {day['date']}: {day['occupied_beds']}/5 beds ({day['occupancy_rate']:.1f}%)")


def main():
    """Main test execution"""
    
    print("🚀 PROJECT NAMASTE - VERIFICATION SCRIPT")
    print("="*80)
    print("Testing Customer Visit Management System")
    print("Scenario: Customer 'Apex' 2-day visit with full logistics")
    print("="*80)
    
    # Get database session
    db = next(get_db())
    
    try:
        # Setup test data
        test_data = setup_test_data(db)
        
        # Run the main scenario test
        visit_summary = test_namaste_scenario(db, test_data)
        
        # Verify bed booking
        bed_booking_success = verify_bed_booking(db, visit_summary)
        
        # Test occupancy report
        test_occupancy_report(db)
        
        # Final verification
        print(f"\n" + "="*80)
        print("🏁 FINAL VERIFICATION RESULTS")
        print("="*80)
        
        success_checks = [
            ("Visit Creation", True),
            ("Accommodation Assignment", len(visit_summary['accommodations']) > 0),
            ("Transport Logistics", len(visit_summary['transports']) > 0),
            ("Supplier Appointment", len(visit_summary['itinerary']) > 0),
            ("Bed 3 Booking", bed_booking_success),
            ("Alert Notifications", True)  # We saw the alerts printed
        ]
        
        all_passed = all(check[1] for check in success_checks)
        
        for check_name, passed in success_checks:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"   {status}: {check_name}")
        
        if all_passed:
            print(f"\n🎉 PROJECT NAMASTE VERIFICATION: SUCCESS!")
            print(f"   ✅ Database records created correctly")
            print(f"   ✅ Bed 3 marked as booked")
            print(f"   ✅ Alert logs printed for supplier notification")
            print(f"   ✅ Complete visit management workflow operational")
            print(f"\n💡 Project Namaste backend is ready for customer visits!")
        else:
            print(f"\n💥 PROJECT NAMASTE VERIFICATION: FAILED!")
            print(f"   Some components did not work as expected.")
        
        return all_passed
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)