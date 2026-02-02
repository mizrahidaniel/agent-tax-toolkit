"""Main tax compliance orchestration."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .crypto import TINEncryption
from .models import Base, Contractor, Payment


class TaxCompliance:
    """Main interface for tax compliance operations."""

    def __init__(
        self,
        database_url: str = "sqlite:///./agent_tax.db",
        stripe_key: Optional[str] = None,
        irs_tin: Optional[str] = None,
        tin_encryption_key: Optional[bytes] = None,
    ):
        """Initialize tax compliance engine.
        
        Args:
            database_url: SQLAlchemy database URL
            stripe_key: Stripe API key (for payment data)
            irs_tin: Your IRS Tax ID Number (for 1099 filing)
            tin_encryption_key: Encryption key for TINs
        """
        # Database setup
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        
        # Configuration
        self.stripe_key = stripe_key
        self.irs_tin = irs_tin
        
        # Encryption
        if tin_encryption_key:
            self.crypto = TINEncryption(tin_encryption_key)
        else:
            self.crypto = TINEncryption.from_env()

    def get_db(self) -> Session:
        """Get database session."""
        return self.SessionLocal()

    def add_contractor(
        self,
        name: str,
        email: str,
        tin: Optional[str] = None,
        address: Optional[str] = None,
        city: Optional[str] = None,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
    ) -> Contractor:
        """Add a new contractor.
        
        Args:
            name: Contractor full name
            email: Contractor email
            tin: Tax ID Number (encrypted before storage)
            address: Street address
            city: City
            state: 2-letter state code
            zip_code: ZIP code
            
        Returns:
            Created contractor
        """
        db = self.get_db()
        try:
            contractor = Contractor(
                name=name,
                email=email,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code,
            )
            
            if tin:
                contractor.tin_encrypted = self.crypto.encrypt(tin)
                contractor.w9_received = True
                contractor.w9_received_date = date.today()
            
            db.add(contractor)
            db.commit()
            db.refresh(contractor)
            
            return contractor
        finally:
            db.close()

    def add_payment(
        self,
        contractor_id: str,
        amount: Decimal,
        payment_date: date,
        description: Optional[str] = None,
        stripe_payment_id: Optional[str] = None,
        category: str = "contractor_payment",
    ) -> Payment:
        """Record a payment to a contractor.
        
        Args:
            contractor_id: Contractor ID
            amount: Payment amount
            payment_date: Payment date
            description: Payment description
            stripe_payment_id: Stripe payment ID
            category: Payment category
            
        Returns:
            Created payment
        """
        db = self.get_db()
        try:
            payment = Payment(
                contractor_id=contractor_id,
                amount=amount,
                date=payment_date,
                description=description,
                stripe_payment_id=stripe_payment_id,
                category=category,
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            return payment
        finally:
            db.close()

    def get_contractor_total(self, contractor_id: str, year: Optional[int] = None) -> Decimal:
        """Get total paid to a contractor.
        
        Args:
            contractor_id: Contractor ID
            year: Filter by year (None = all time)
            
        Returns:
            Total amount paid
        """
        db = self.get_db()
        try:
            query = db.query(Payment).filter(Payment.contractor_id == contractor_id)
            
            if year:
                query = query.filter(Payment.date >= date(year, 1, 1))
                query = query.filter(Payment.date <= date(year, 12, 31))
            
            payments = query.all()
            return sum(p.amount for p in payments)
        finally:
            db.close()

    def has_w9(self, contractor_id: str) -> bool:
        """Check if contractor has submitted W-9.
        
        Args:
            contractor_id: Contractor ID
            
        Returns:
            True if W-9 received
        """
        db = self.get_db()
        try:
            contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
            return contractor.w9_received if contractor else False
        finally:
            db.close()

    def get_contractors_above_threshold(self, year: int, threshold: Decimal = Decimal("600")) -> list[dict]:
        """Get contractors earning above threshold (require 1099).
        
        Args:
            year: Tax year
            threshold: Threshold amount (default $600)
            
        Returns:
            List of contractors with total_paid
        """
        db = self.get_db()
        try:
            contractors = db.query(Contractor).all()
            
            results = []
            for contractor in contractors:
                total = self.get_contractor_total(contractor.id, year)
                if total >= threshold:
                    results.append({
                        "contractor": contractor,
                        "total_paid": total,
                    })
            
            return results
        finally:
            db.close()
