"""
Database Seeding Script for Real Estate Manager (Django Backend)
Populates realistic dummy projects, inventory plots, contacts, expenses,
shared expenses, leads, deals, follow-ups, and transactions.
"""
import os
import sys
import django
from decimal import Decimal
from datetime import date, datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.utils import timezone
from core.models import (
    Project, Site, Contact, Lead, LandDeal, FollowUp,
    Activity, Transaction, Expense, ExpenseCategory,
    SharedPurpose, SharedExpense, ExpenseSplit, Settlement
)

def populate():
    print("=" * 60)
    print("Seeding Database with Realistic Demonstration Data...")
    print("=" * 60)

    # 1. Clean existing records (optional, preserves superusers)
    print("Clearing old transactional demo records...")
    ExpenseSplit.objects.all().delete()
    Settlement.objects.all().delete()
    SharedExpense.objects.all().delete()
    SharedPurpose.objects.all().delete()
    FollowUp.objects.all().delete()
    Lead.objects.all().delete()
    LandDeal.objects.all().delete()
    Transaction.objects.all().delete()
    Expense.objects.all().delete()
    Site.objects.all().delete()
    Project.objects.all().delete()
    Contact.objects.all().delete()
    ExpenseCategory.objects.all().delete()
    Activity.objects.all().delete()

    # 2. Seed Contacts
    print("Seeding Contacts (Partners, Investors, Customers, Landowners, Brokers, Vendors)...")
    partners = [
        Contact.objects.create(name="Rahul Sharma", mobile="9845012345", email="rahul@reman.com", contact_type="Partner", ownership_percentage=Decimal('40.00'), location="Bangalore"),
        Contact.objects.create(name="Vikram Patel", mobile="9845023456", email="vikram@reman.com", contact_type="Partner", ownership_percentage=Decimal('35.00'), location="Bangalore"),
        Contact.objects.create(name="Anita Desai", mobile="9845034567", email="anita@reman.com", contact_type="Partner", ownership_percentage=Decimal('25.00'), location="Bangalore"),
    ]

    investors = [
        Contact.objects.create(name="Suresh Reddy", mobile="9845045678", email="suresh@invest.com", contact_type="Investor", location="Hyderabad"),
        Contact.objects.create(name="Kiran Rao", mobile="9845056789", email="kiran@invest.com", contact_type="Investor", location="Mumbai"),
    ]

    landowners = [
        Contact.objects.create(name="Gowda Landowner", mobile="9845067890", contact_type="Landowner", location="North Bangalore"),
        Contact.objects.create(name="Ramesh K", mobile="9845078901", contact_type="Landowner", location="Devenahalli"),
    ]

    customers = [
        Contact.objects.create(name="Deepak Verma", mobile="9845089012", email="deepak@gmail.com", contact_type="Customer", location="Whitefield"),
        Contact.objects.create(name="Priya Nair", mobile="9845090123", email="priya@gmail.com", contact_type="Customer", location="Indiranagar"),
        Contact.objects.create(name="Manish Gupta", mobile="9845091234", email="manish@gmail.com", contact_type="Customer", location="Koramangala"),
        Contact.objects.create(name="Sneha Rao", mobile="9845092345", email="sneha@gmail.com", contact_type="Customer", location="HSR Layout"),
        Contact.objects.create(name="Rohan Joshi", mobile="9845093456", email="rohan@gmail.com", contact_type="Customer", location="JP Nagar"),
    ]

    brokers = [
        Contact.objects.create(name="Balaji Realty", mobile="9845094567", contact_type="Broker", location="Bangalore"),
    ]

    vendors = [
        Contact.objects.create(name="Apex Earthmovers", mobile="9845095678", contact_type="Vendor", location="Yelahanka"),
        Contact.objects.create(name="Surabhi Surveyors", mobile="9845096789", contact_type="Vendor", location="Hebbal"),
    ]

    # 3. Seed Projects
    print("Seeding Master Projects...")
    proj1 = Project.objects.create(
        project_name="Greenfield Meadows",
        location="Yelahanka, North Bangalore",
        landowner=landowners[0],
        survey_number="Sy No. 42/1, 42/2",
        land_area="15 Acres",
        purchase_cost=Decimal('18000000.00'),
        development_cost=Decimal('3500000.00'),
        status="Development",
        notes="Premium villa plot community with 40ft wide blacktop roads."
    )

    proj2 = Project.objects.create(
        project_name="Skyline Heights Enclave",
        location="Whitefield Extension",
        landowner=landowners[1],
        survey_number="Sy No. 108/3",
        land_area="10 Acres",
        purchase_cost=Decimal('14000000.00'),
        development_cost=Decimal('2800000.00'),
        status="Sales in Progress",
        notes="BDA approved plotted layout near IT corridor."
    )

    proj3 = Project.objects.create(
        project_name="Royal Palms Layout",
        location="Devenahalli Airport Corridor",
        landowner=landowners[0],
        survey_number="Sy No. 77/5",
        land_area="20 Acres",
        purchase_cost=Decimal('25000000.00'),
        development_cost=Decimal('4200000.00'),
        status="Planning",
        notes="High appreciation investment layout close to SEZ."
    )

    # 4. Seed Site Inventory Plots
    print("Seeding Site Inventory Plots...")
    plots_data = [
        # Project 1: Greenfield Meadows
        (proj1, "A-101", "1200 sqft", "30x40", "East", "40ft", Decimal('2400000.00'), "Sold", customers[0]),
        (proj1, "A-102", "1200 sqft", "30x40", "East", "40ft", Decimal('2400000.00'), "Sold", customers[1]),
        (proj1, "A-103", "1500 sqft", "30x50", "North", "40ft", Decimal('3000000.00'), "Booked", customers[2]),
        (proj1, "A-104", "1500 sqft", "30x50", "North", "40ft", Decimal('3000000.00'), "Blocked", None),
        (proj1, "A-105", "2400 sqft", "40x60", "East", "60ft", Decimal('4800000.00'), "Available", None),
        (proj1, "A-106", "2400 sqft", "40x60", "West", "60ft", Decimal('4800000.00'), "Available", None),
        (proj1, "A-107", "1200 sqft", "30x40", "North", "30ft", Decimal('2400000.00'), "Available", None),
        (proj1, "A-108", "1500 sqft", "30x50", "South", "30ft", Decimal('3000000.00'), "Available", None),
        # Project 2: Skyline Heights
        (proj2, "B-201", "1200 sqft", "30x40", "East", "30ft", Decimal('2700000.00'), "Sold", customers[3]),
        (proj2, "B-202", "1200 sqft", "30x40", "West", "30ft", Decimal('2700000.00'), "Sold", customers[4]),
        (proj2, "B-203", "1500 sqft", "30x50", "North", "40ft", Decimal('3400000.00'), "Booked", customers[0]),
        (proj2, "B-204", "1500 sqft", "30x50", "East", "40ft", Decimal('3400000.00'), "Blocked", customers[1]),
        (proj2, "B-205", "2400 sqft", "40x60", "North", "40ft", Decimal('5400000.00'), "Available", None),
        (proj2, "B-206", "1800 sqft", "30x60", "East", "30ft", Decimal('4050000.00'), "Available", None),
        # Project 3: Royal Palms Layout
        (proj3, "C-301", "1200 sqft", "30x40", "East", "40ft", Decimal('2100000.00'), "Available", None),
        (proj3, "C-302", "1200 sqft", "30x40", "West", "40ft", Decimal('2100000.00'), "Available", None),
        (proj3, "C-303", "1500 sqft", "30x50", "North", "40ft", Decimal('2600000.00'), "Available", None),
        (proj3, "C-304", "2400 sqft", "40x60", "East", "60ft", Decimal('4200000.00'), "Available", None),
    ]

    for p, num, area, dim, facing, road, price, status, cust in plots_data:
        Site.objects.create(
            project=p,
            site_number=num,
            area=area,
            dimensions=dim,
            facing=facing,
            road_width=road,
            price=price,
            status=status,
            customer=cust
        )

    # 5. Seed Expense Categories & Business Expenses
    print("Seeding Expense Categories & Business Expenses...")
    cat_dev, _ = ExpenseCategory.objects.get_or_create(name='Site Leveling & Earthwork')
    cat_legal, _ = ExpenseCategory.objects.get_or_create(name='Legal & Registration')
    cat_roads, _ = ExpenseCategory.objects.get_or_create(name='Road Construction & Drainage')
    cat_mkt, _ = ExpenseCategory.objects.get_or_create(name='Marketing & Hoardings')
    cat_elec, _ = ExpenseCategory.objects.get_or_create(name='Electricity & Cabling')
    cat_office, _ = ExpenseCategory.objects.get_or_create(name='Office Supplies & Administration')

    # Seed Paid expenses (triggers transaction automation) and To Be Paid expenses
    today = date.today()
    expenses_to_seed = [
        (proj1, Decimal('450000.00'), cat_dev, "Phase 1 Grading and Earthwork by Apex", "Paid", "Rahul Sharma", "Bank Transfer", today - timedelta(days=20)),
        (proj1, Decimal('180000.00'), cat_legal, "Government layout sanction fees and legal verification", "Paid", "Vikram Patel", "UPI", today - timedelta(days=15)),
        (proj1, Decimal('850000.00'), cat_roads, "Asphalt road laying 40ft main boulevard", "To Be Paid", "Apex Earthmovers", "Bank Transfer", today - timedelta(days=5)),
        (proj2, Decimal('320000.00'), cat_mkt, "Digital Lead Generation Campaign & Highway Hoardings", "Paid", "Anita Desai", "Card", today - timedelta(days=10)),
        (proj2, Decimal('150000.00'), cat_elec, "Underground cabling transformer setup advance", "To Be Paid", "BESCOM Vendor", "Cheque", today - timedelta(days=2)),
        (proj3, Decimal('75000.00'), cat_office, "Site office furniture and setup expenses", "Paid", "Rahul Sharma", "Cash", today - timedelta(days=12)),
    ]

    for proj, amt, cat, desc, status, payer, meth, exp_date in expenses_to_seed:
        Expense.objects.create(
            project=proj,
            amount=amt,
            category=cat,
            description=desc,
            status=status,
            paid_by=payer,
            payment_method=meth,
            date=exp_date
        )

    # 6. Seed Partner Capital Investments & Received Transactions
    print("Seeding Capital Investments & Received Site Sale Transactions...")
    # Partner capital contributions
    Transaction.objects.create(project=proj1, transaction_type="Paid", amount=Decimal('6000000.00'), payment_type="Investment", paid_by="Rahul Sharma", notes="Initial capital contribution for Greenfield Meadows")
    Transaction.objects.create(project=proj1, transaction_type="Paid", amount=Decimal('5000000.00'), payment_type="Investment", paid_by="Vikram Patel", notes="Initial capital contribution for Greenfield Meadows")
    Transaction.objects.create(project=proj1, transaction_type="Paid", amount=Decimal('4000000.00'), payment_type="Investment", paid_by="Anita Desai", notes="Initial capital contribution for Greenfield Meadows")
    Transaction.objects.create(project=proj2, transaction_type="Paid", amount=Decimal('4000000.00'), payment_type="Investment", paid_by="Rahul Sharma", notes="Equity investment Skyline Heights")

    # Received payments from site buyers
    Transaction.objects.create(project=proj1, contact=customers[0], transaction_type="Received", amount=Decimal('2400000.00'), payment_type="Site Sale", paid_by=customers[0].name, notes="Full payment for Plot A-101")
    Transaction.objects.create(project=proj1, contact=customers[1], transaction_type="Received", amount=Decimal('2400000.00'), payment_type="Site Sale", paid_by=customers[1].name, notes="Full payment for Plot A-102")
    Transaction.objects.create(project=proj1, contact=customers[2], transaction_type="Received", amount=Decimal('500000.00'), payment_type="Booking Advance", paid_by=customers[2].name, notes="Booking advance for Plot A-103")
    Transaction.objects.create(project=proj2, contact=customers[3], transaction_type="Received", amount=Decimal('2700000.00'), payment_type="Site Sale", paid_by=customers[3].name, notes="Full payment for Plot B-201")
    Transaction.objects.create(project=proj2, contact=customers[4], transaction_type="Received", amount=Decimal('2700000.00'), payment_type="Site Sale", paid_by=customers[4].name, notes="Full payment for Plot B-202")

    # 7. Seed Shared Expenses (Splitwise Module)
    print("Seeding Shared Expenses (Splitwise Group, Splits & Settlements)...")
    purpose1 = SharedPurpose.objects.create(
        project=proj1,
        name="Phase 1 Joint Site Leveling & Fencing",
        notes="Shared site infrastructure costs divided between primary project partners."
    )
    purpose1.participants.set([partners[0], partners[1], partners[2]])

    # Expense 1: Paid by Rahul Sharma (300,000 Equal split)
    sh_exp1 = SharedExpense.objects.create(
        purpose=purpose1,
        description="Heavy Earthmover Rental for Site Grading",
        category="Earthwork",
        total_amount=Decimal('300000.00'),
        paid_by=partners[0],
        split_method="Equal",
        date=today - timedelta(days=14)
    )
    ExpenseSplit.objects.create(shared_expense=sh_exp1, participant=partners[0], amount=Decimal('100000.00'))
    ExpenseSplit.objects.create(shared_expense=sh_exp1, participant=partners[1], amount=Decimal('100000.00'))
    ExpenseSplit.objects.create(shared_expense=sh_exp1, participant=partners[2], amount=Decimal('100000.00'))

    # Expense 2: Paid by Vikram Patel (150,000 Exact split)
    sh_exp2 = SharedExpense.objects.create(
        purpose=purpose1,
        description="Surveying Equipment & Boundary Pillars",
        category="Surveying",
        total_amount=Decimal('150000.00'),
        paid_by=partners[1],
        split_method="Exact",
        date=today - timedelta(days=7)
    )
    ExpenseSplit.objects.create(shared_expense=sh_exp2, participant=partners[0], amount=Decimal('50000.00'))
    ExpenseSplit.objects.create(shared_expense=sh_exp2, participant=partners[1], amount=Decimal('50000.00'))
    ExpenseSplit.objects.create(shared_expense=sh_exp2, participant=partners[2], amount=Decimal('50000.00'))

    # Settlement: Anita Desai settles 50,000 with Rahul Sharma
    Settlement.objects.create(
        purpose=purpose1,
        from_person=partners[2],
        to_person=partners[0],
        amount=Decimal('50000.00'),
        payment_method="UPI",
        note="Partial balance settlement for earthwork share"
    )

    # 8. Seed Land Deals
    print("Seeding Land Deals Pipeline...")
    LandDeal.objects.create(
        deal_name="Airport Road 12-Acre Parcel",
        landowner=landowners[0],
        location="Near Bangalore International Airport",
        survey_number="Sy No. 95/1A",
        land_area="12 Acres",
        expected_price=Decimal('16000000.00'),
        offered_price=Decimal('14500000.00'),
        negotiated_price=Decimal('15000000.00'),
        status="Negotiation",
        notes="Strategic commercial land deal undergoing title scrutiny."
    )

    LandDeal.objects.create(
        deal_name="Hoskote Highway Land",
        landowner=landowners[1],
        location="Old Madras Road, Hoskote",
        survey_number="Sy No. 34/2",
        land_area="8 Acres",
        expected_price=Decimal('9500000.00'),
        status="Discussion",
        notes="Initial discussions with agricultural landowners."
    )

    # Closed deal demonstrating automation: auto-instantiates new Project!
    print("Testing Automation: Creating Deal Closed land parcel...")
    LandDeal.objects.create(
        deal_name="Nelamangala Industrial Green Plots",
        landowner=landowners[0],
        location="Nelamangala Highway, Tumkur Road",
        survey_number="Sy No. 120/4",
        land_area="18 Acres",
        expected_price=Decimal('22000000.00'),
        negotiated_price=Decimal('21000000.00'),
        status="Deal Closed",
        notes="Final agreement registered with full documentation."
    )

    # 9. Seed Leads
    print("Seeding Customer Leads Pipeline...")
    now = timezone.now()
    Lead.objects.create(
        name="Arjun Kapoor",
        phone="9845097890",
        project=proj1,
        source="Meta Ads",
        location="Kalyan Nagar",
        interested_property="1500 sqft North Facing Plot",
        status="Follow-up",
        next_follow_up=now + timedelta(hours=3),
        notes="Interested in Greenfield Meadows Plot A-103."
    )

    Lead.objects.create(
        name="Meera Sundaram",
        phone="9845098901",
        project=proj2,
        source="Google Search",
        location="Whitefield",
        interested_property="Villa Plot 40x60",
        status="Interested",
        next_follow_up=now - timedelta(days=1),  # Overdue follow-up
        notes="Scheduled property visit postponed; needs re-engagement."
    )

    # Converted lead demonstrating automation: auto-creates Contact and Deal entry!
    print("Testing Automation: Creating Converted Lead...")
    Lead.objects.create(
        name="Siddharth Menon",
        phone="9845099012",
        project=proj1,
        source="Referral",
        location="Indiranagar",
        interested_property="Corner Plot Greenfield Meadows",
        status="Converted",
        notes="Converted to purchase agreement. Ready to proceed."
    )

    # 10. Seed Follow-ups
    print("Seeding Follow-up Calendar Reminders...")
    FollowUp.objects.create(
        project=proj1,
        related_to="Lead: Arjun Kapoor",
        date=today,
        time="11:30:00",
        reason="Follow up on plot layout sanction copy",
        note="Client requested soft copy of BDA approval letter.",
        status="Pending"
    )

    FollowUp.objects.create(
        project=proj2,
        related_to="Lead: Meera Sundaram",
        date=today - timedelta(days=1),
        time="15:00:00",
        reason="Confirm weekend site visit cab arrangement",
        note="Overdue follow-up for Whitefield layout visit.",
        status="Pending"
    )

    FollowUp.objects.create(
        project=proj1,
        related_to="Vendor: Apex Earthmovers",
        date=today + timedelta(days=2),
        time="10:00:00",
        reason="Site inspection for 40ft road drainage completion",
        note="Milestone verification before releasing final road construction payment.",
        status="Pending"
    )

    print("\n" + "=" * 60)
    print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"Projects: {Project.objects.count()}")
    print(f"Site Inventory Plots: {Site.objects.count()} (Sold: {Site.objects.filter(status='Sold').count()}, Available: {Site.objects.filter(status='Available').count()})")
    print(f"Contacts: {Contact.objects.count()} (Partners: {Contact.objects.filter(contact_type='Partner').count()})")
    print(f"Expenses: {Expense.objects.count()}")
    print(f"Transactions: {Transaction.objects.count()}")
    print(f"Land Deals: {LandDeal.objects.count()}")
    print(f"Leads: {Lead.objects.count()}")
    print(f"Follow-ups: {FollowUp.objects.count()}")
    print(f"Shared Purposes: {SharedPurpose.objects.count()} (Expenses: {SharedExpense.objects.count()})")
    print("=" * 60)

if __name__ == '__main__':
    populate()
