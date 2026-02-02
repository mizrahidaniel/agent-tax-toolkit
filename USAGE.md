# Usage Guide - Agent Tax Toolkit

## Quick Start

### 1. Installation

```bash
pip install -e .
```

### 2. Initialize Configuration

```bash
agent-tax init
```

This creates `.env` with:
- Database URL (SQLite by default)
- TIN encryption key (auto-generated)
- Placeholders for Stripe/email credentials

### 3. Start W-9 Portal

```bash
agent-tax serve --port 8000
```

Access at: http://localhost:8000

API docs: http://localhost:8000/docs

## API Endpoints

### Submit W-9 Form

```bash
curl -X POST "http://localhost:8000/api/w9/submit" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Contractor",
    "email": "jane@example.com",
    "tin": "123-45-6789",
    "address": "123 Main St",
    "city": "San Francisco",
    "state": "CA",
    "zip_code": "94102"
  }'
```

**Response:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Jane Contractor",
  "email": "jane@example.com",
  "w9_received": true,
  "w9_received_date": "2026-02-02",
  "created_at": "2026-02-02T08:00:00"
}
```

### List Contractors

```bash
# All contractors
curl "http://localhost:8000/api/contractors"

# Only pending W-9s
curl "http://localhost:8000/api/contractors?w9_received=false"

# Only received W-9s
curl "http://localhost:8000/api/contractors?w9_received=true"
```

### Get Decrypted TIN

```bash
curl "http://localhost:8000/api/contractors/{contractor_id}/tin"
```

**Response:**
```json
{
  "contractor_id": "550e8400-e29b-41d4-a716-446655440000",
  "tin": "123-45-6789"
}
```

⚠️ **Security:** Protect this endpoint in production (auth required).

## Python SDK Usage

### Basic Setup

```python
from agent_tax_toolkit import TaxCompliance
from decimal import Decimal
from datetime import date

# Initialize
tax = TaxCompliance(
    database_url="sqlite:///./agent_tax.db",
    stripe_key="sk_test_...",
    irs_tin="12-3456789"
)

# Add contractor
contractor = tax.add_contractor(
    name="Jane Contractor",
    email="jane@example.com",
    tin="123-45-6789",
    address="123 Main St",
    city="San Francisco",
    state="CA",
    zip_code="94102"
)

print(f"Created contractor: {contractor.id}")
```

### Record Payments

```python
# Add payment
payment = tax.add_payment(
    contractor_id=contractor.id,
    amount=Decimal("1500.00"),
    payment_date=date(2026, 1, 15),
    description="Consulting services - January",
    category="contractor_payment"
)

# Check total paid
total = tax.get_contractor_total(contractor.id, year=2026)
print(f"Total paid in 2026: ${total}")
```

### Check W-9 Status

```python
# Check if W-9 received
if tax.has_w9(contractor.id):
    print("✅ W-9 received")
else:
    print("⚠️ W-9 pending - send reminder")
```

### Find Contractors Requiring 1099s

```python
# Get all contractors earning $600+ in 2026
contractors_1099 = tax.get_contractors_above_threshold(
    year=2026,
    threshold=Decimal("600")
)

print(f"Found {len(contractors_1099)} contractors requiring 1099s")

for item in contractors_1099:
    contractor = item["contractor"]
    total = item["total_paid"]
    print(f"- {contractor.name}: ${total}")
```

## Integration with Revenue Ecosystem

### SaaS Starter Kit Integration

```python
from paas_starter import PayAsYouGoService
from agent_tax_toolkit import TaxCompliance

service = PayAsYouGoService(...)
tax = TaxCompliance(stripe_key=STRIPE_KEY, irs_tin=YOUR_TIN)

# Auto-trigger W-9 collection at $600
@service.on_revenue_milestone(600)
async def collect_w9(customer_id, total_paid):
    # Check if W-9 already received
    if not tax.has_w9(customer_id):
        # Send W-9 request email
        send_w9_request(
            email=get_customer_email(customer_id),
            portal_url=f"https://w9.yourdomain.com?id={customer_id}"
        )
```

### Stripe Webhook Integration

```python
from fastapi import FastAPI, Request
from agent_tax_toolkit import TaxCompliance

app = FastAPI()
tax = TaxCompliance(stripe_key=STRIPE_KEY)

@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    event = await request.json()
    
    if event["type"] == "payment_intent.succeeded":
        payment = event["data"]["object"]
        
        # Record payment
        tax.add_payment(
            contractor_id=payment["metadata"]["contractor_id"],
            amount=Decimal(str(payment["amount"] / 100)),
            payment_date=date.today(),
            stripe_payment_id=payment["id"],
            category="contractor_payment"
        )
        
        # Check if W-9 needed
        total = tax.get_contractor_total(payment["metadata"]["contractor_id"], year=2026)
        if total >= 600 and not tax.has_w9(payment["metadata"]["contractor_id"]):
            send_w9_reminder(payment["metadata"]["contractor_id"])
    
    return {"status": "success"}
```

## Next Steps

### Phase 2: 1099 Generation (Coming Soon)

```python
# Generate 1099s for all contractors
from agent_tax_toolkit import Form1099Generator

generator = Form1099Generator(tax)
forms = generator.generate_all(year=2026)

for form in forms:
    print(f"Generated 1099 for {form.contractor.name}")
    
    # E-file with IRS
    confirmation = generator.efile(form)
    print(f"E-filed: {confirmation}")
    
    # Send to contractor
    generator.send_to_contractor(form, methods=["email", "postal"])
```

### Phase 3: VAT Handler (Coming Soon)

```python
from agent_tax_toolkit import VATHandler

vat = VATHandler(taxjar_key=TAXJAR_KEY)

# Calculate VAT on invoice
tax_rate = vat.get_rate(
    country="GB",  # United Kingdom
    customer_type="business"
)

invoice_total = amount + (amount * tax_rate)
```

## Security Best Practices

### 1. TIN Encryption
- **Never** store TINs in plaintext
- Rotate encryption keys annually
- Store keys in secure vault (AWS Secrets Manager, 1Password, etc.)

### 2. Access Control
- Protect `/api/contractors/{id}/tin` endpoint (auth required)
- Log all TIN decryption attempts
- Implement rate limiting

### 3. Compliance
- **SOC 2** compliance for PII handling
- **GDPR** for EU contractors
- Annual security audits

## Troubleshooting

### "TIN_ENCRYPTION_KEY not set"

Run `agent-tax init` to generate `.env` file with encryption key.

### "Database locked" (SQLite)

SQLite doesn't support concurrent writes. For production, use PostgreSQL:

```bash
# .env
DATABASE_URL=postgresql://user:pass@localhost/agent_tax
```

### "Invalid TIN format"

TINs must be 9 digits (with or without dashes):
- SSN: `123-45-6789` or `123456789`
- EIN: `12-3456789` or `123456789`

## Support

- **GitHub Issues:** https://github.com/mizrahidaniel/agent-tax-toolkit/issues
- **ClawBoard Task:** https://clawboard.io/tasks/330001
- **Email:** agent@clawboard.io
