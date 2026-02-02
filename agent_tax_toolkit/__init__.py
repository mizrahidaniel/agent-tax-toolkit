"""Agent Tax Toolkit - Automate tax compliance for AI agents."""

__version__ = "0.1.0"

from .compliance import TaxCompliance
from .models import Contractor, Payment, Form1099

__all__ = ["TaxCompliance", "Contractor", "Payment", "Form1099"]
