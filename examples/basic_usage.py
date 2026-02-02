"""Basic usage example for Agent Tax Toolkit."""

from agent_tax_toolkit import TaxCompliance
from decimal import Decimal
from datetime import date
import os

# Set encryption key (would normally be in .env)
os.environ["TIN_ENCRYPTION_KEY"] = "test_key_for_demo_only_32_bytes_"

def main():
    print("🚀 Agent Tax Toolkit - Basic Usage Example\n")
    
    # Initialize tax compliance
    print("1️⃣ Initializing tax compliance engine...")
    tax = TaxCompliance(
        database_url="sqlite:///./example_tax.db",
        irs_tin="12-3456789"
    )
    print("✅ Initialized\n")
    
    # Add contractors
    print("2️⃣ Adding contractors...")
    
    jane = tax.add_contractor(
        name="Jane Contractor",
        email="jane@example.com",
        tin="123-45-6789",
        address="123 Main St",
        city="San Francisco",
        state="CA",
        zip_code="94102"
    )
    print(f"✅ Added Jane Contractor (ID: {jane.id})")
    
    john = tax.add_contractor(
        name="John Freelancer",
        email="john@example.com",
        # No TIN yet (W-9 pending)
        address="456 Oak Ave",
        city="Austin",
        state="TX",
        zip_code="78701"
    )
    print(f"✅ Added John Freelancer (ID: {john.id})\n")
    
    # Record payments
    print("3️⃣ Recording payments...")
    
    # Jane - $800 in January
    payment1 = tax.add_payment(
        contractor_id=jane.id,
        amount=Decimal("800.00"),
        payment_date=date(2026, 1, 15),
        description="Consulting services - January"
    )
    print(f"✅ Recorded $800 payment to Jane")
    
    # Jane - $500 in February  
    payment2 = tax.add_payment(
        contractor_id=jane.id,
        amount=Decimal("500.00"),
        payment_date=date(2026, 2, 1),
        description="Consulting services - February"
    )
    print(f"✅ Recorded $500 payment to Jane")
    
    # John - $300 (below $600 threshold)
    payment3 = tax.add_payment(
        contractor_id=john.id,
        amount=Decimal("300.00"),
        payment_date=date(2026, 1, 20),
        description="Design work"
    )
    print(f"✅ Recorded $300 payment to John\n")
    
    # Check totals
    print("4️⃣ Checking payment totals...")
    
    jane_total = tax.get_contractor_total(jane.id, year=2026)
    john_total = tax.get_contractor_total(john.id, year=2026)
    
    print(f"📊 Jane total (2026): ${jane_total}")
    print(f"📊 John total (2026): ${john_total}\n")
    
    # Check W-9 status
    print("5️⃣ Checking W-9 status...")
    
    if tax.has_w9(jane.id):
        print("✅ Jane: W-9 received")
    else:
        print("⚠️  Jane: W-9 pending")
    
    if tax.has_w9(john.id):
        print("✅ John: W-9 received")
    else:
        print("⚠️  John: W-9 pending - send reminder!\n")
    
    # Find contractors requiring 1099s
    print("6️⃣ Finding contractors requiring 1099s (>= $600)...")
    
    contractors_1099 = tax.get_contractors_above_threshold(
        year=2026,
        threshold=Decimal("600")
    )
    
    print(f"📋 Found {len(contractors_1099)} contractors requiring 1099s:\n")
    
    for item in contractors_1099:
        contractor = item["contractor"]
        total = item["total_paid"]
        w9_status = "✅ W-9 received" if contractor.w9_received else "⚠️  W-9 pending"
        
        print(f"   • {contractor.name}")
        print(f"     Total paid: ${total}")
        print(f"     Status: {w9_status}")
        print(f"     Email: {contractor.email}\n")
    
    print("✨ Example complete!")
    print("\n💡 Next steps:")
    print("   1. Start W-9 portal: agent-tax serve")
    print("   2. Send W-9 requests to pending contractors")
    print("   3. Generate 1099s at end of year (Phase 2)")


if __name__ == "__main__":
    main()
