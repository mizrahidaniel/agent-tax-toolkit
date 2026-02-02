"""Basic tests for Agent Tax Toolkit."""

import os
import pytest
from decimal import Decimal
from datetime import date

from agent_tax_toolkit import TaxCompliance
from agent_tax_toolkit.crypto import TINEncryption

# Set test encryption key
os.environ["TIN_ENCRYPTION_KEY"] = "test_encryption_key_32_bytes_123"


def test_encryption():
    """Test TIN encryption/decryption."""
    crypto = TINEncryption.from_env()
    
    # Encrypt
    tin = "123-45-6789"
    encrypted = crypto.encrypt(tin)
    
    # Decrypt
    decrypted = crypto.decrypt(encrypted)
    assert decrypted == "123456789"  # Dashes removed
    
    # Format
    formatted = crypto.format_tin(decrypted, type="ssn")
    assert formatted == "123-45-6789"


def test_add_contractor():
    """Test adding a contractor."""
    tax = TaxCompliance(database_url="sqlite:///:memory:")
    
    contractor = tax.add_contractor(
        name="Test Contractor",
        email="test@example.com",
        tin="123-45-6789",
        address="123 Test St",
        city="Test City",
        state="CA",
        zip_code="12345"
    )
    
    assert contractor.name == "Test Contractor"
    assert contractor.email == "test@example.com"
    assert contractor.w9_received is True
    assert contractor.tin_encrypted is not None


def test_payment_tracking():
    """Test payment recording and totals."""
    tax = TaxCompliance(database_url="sqlite:///:memory:")
    
    # Add contractor
    contractor = tax.add_contractor(
        name="Test Contractor",
        email="test@example.com"
    )
    
    # Add payments
    tax.add_payment(
        contractor_id=contractor.id,
        amount=Decimal("500.00"),
        payment_date=date(2026, 1, 15)
    )
    
    tax.add_payment(
        contractor_id=contractor.id,
        amount=Decimal("300.00"),
        payment_date=date(2026, 2, 1)
    )
    
    # Check total
    total = tax.get_contractor_total(contractor.id, year=2026)
    assert total == Decimal("800.00")


def test_1099_threshold():
    """Test finding contractors above 1099 threshold."""
    tax = TaxCompliance(database_url="sqlite:///:memory:")
    
    # Add two contractors
    c1 = tax.add_contractor(name="Contractor 1", email="c1@example.com")
    c2 = tax.add_contractor(name="Contractor 2", email="c2@example.com")
    
    # Pay c1 $700 (above threshold)
    tax.add_payment(
        contractor_id=c1.id,
        amount=Decimal("700.00"),
        payment_date=date(2026, 1, 15)
    )
    
    # Pay c2 $400 (below threshold)
    tax.add_payment(
        contractor_id=c2.id,
        amount=Decimal("400.00"),
        payment_date=date(2026, 1, 20)
    )
    
    # Find contractors above $600 threshold
    contractors = tax.get_contractors_above_threshold(year=2026, threshold=Decimal("600"))
    
    assert len(contractors) == 1
    assert contractors[0]["contractor"].name == "Contractor 1"
    assert contractors[0]["total_paid"] == Decimal("700.00")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
