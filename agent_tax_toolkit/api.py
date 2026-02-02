"""FastAPI app for W-9 collection portal."""

from datetime import date
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from .crypto import TINEncryption
from .models import Base, Contractor

app = FastAPI(
    title="Agent Tax Toolkit - W-9 Portal",
    description="Automated tax compliance for AI agents",
    version="0.1.0",
)

# Database setup
DATABASE_URL = "sqlite:///./agent_tax.db"  # Default to SQLite for MVP
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Encryption
tin_crypto = TINEncryption.from_env()


def get_db():
    """Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Request models
class W9FormRequest(BaseModel):
    """W-9 form submission data."""

    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    tin: str = Field(..., min_length=9, max_length=11, description="SSN or EIN (with or without dashes)")
    address: str
    city: str
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., min_length=5, max_length=10)


class ContractorResponse(BaseModel):
    """Contractor response data."""

    id: str
    name: str
    email: str
    w9_received: bool
    w9_received_date: Optional[date]
    created_at: date

    class Config:
        from_attributes = True


# Endpoints
@app.get("/")
async def root():
    """Health check."""
    return {
        "service": "Agent Tax Toolkit",
        "status": "running",
        "version": "0.1.0",
    }


@app.post("/api/w9/submit", response_model=ContractorResponse)
async def submit_w9(form: W9FormRequest, db: Session = Depends(get_db)):
    """Submit W-9 form.
    
    Creates or updates contractor with encrypted TIN.
    """
    # Check if contractor exists
    contractor = db.query(Contractor).filter(Contractor.email == form.email).first()
    
    if contractor:
        # Update existing contractor
        contractor.name = form.name
        contractor.tin_encrypted = tin_crypto.encrypt(form.tin)
        contractor.w9_received = True
        contractor.w9_received_date = date.today()
        contractor.address = form.address
        contractor.city = form.city
        contractor.state = form.state
        contractor.zip_code = form.zip_code
    else:
        # Create new contractor
        contractor = Contractor(
            name=form.name,
            email=form.email,
            tin_encrypted=tin_crypto.encrypt(form.tin),
            w9_received=True,
            w9_received_date=date.today(),
            address=form.address,
            city=form.city,
            state=form.state,
            zip_code=form.zip_code,
        )
        db.add(contractor)
    
    db.commit()
    db.refresh(contractor)
    
    return contractor


@app.get("/api/contractors/{contractor_id}", response_model=ContractorResponse)
async def get_contractor(contractor_id: str, db: Session = Depends(get_db)):
    """Get contractor by ID."""
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    return contractor


@app.get("/api/contractors", response_model=list[ContractorResponse])
async def list_contractors(
    w9_received: Optional[bool] = None,
    db: Session = Depends(get_db)
):
    """List all contractors.
    
    Args:
        w9_received: Filter by W-9 status (True=received, False=pending)
    """
    query = db.query(Contractor)
    
    if w9_received is not None:
        query = query.filter(Contractor.w9_received == w9_received)
    
    contractors = query.all()
    return contractors


@app.get("/api/contractors/{contractor_id}/tin")
async def get_contractor_tin(contractor_id: str, db: Session = Depends(get_db)):
    """Get decrypted TIN for a contractor.
    
    ⚠️ SECURITY: This endpoint should be protected in production.
    """
    contractor = db.query(Contractor).filter(Contractor.id == contractor_id).first()
    
    if not contractor:
        raise HTTPException(status_code=404, detail="Contractor not found")
    
    if not contractor.tin_encrypted:
        raise HTTPException(status_code=404, detail="TIN not available")
    
    tin_decrypted = tin_crypto.decrypt(contractor.tin_encrypted)
    tin_formatted = tin_crypto.format_tin(tin_decrypted, type="ssn")
    
    return {
        "contractor_id": contractor.id,
        "tin": tin_formatted,
    }
