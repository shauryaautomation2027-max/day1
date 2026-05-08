from datetime import datetime
from typing import Dict, List


APPROVED_VENDORS = {
    "ACME Corp",
    "XYZ Solutions Pvt Ltd",
    "BrightTech",
}

CREDIT_LIMIT = 10000

ALLOWED_CURRENCIES = {"INR", "USD"}


def validate_invoice(invoice: Dict) -> Dict:
    """
    Validate invoice data.

    Checks:
    - vendor in approved list
    - amount <= credit limit
    - due_date is in future
    - currency is INR/USD
    """

    errors: List[str] = []

    # -----------------------------
    # Vendor Validation
    # -----------------------------
    vendor = invoice.get("vendor")

    if vendor not in APPROVED_VENDORS:
        errors.append("Vendor is not approved")

    # -----------------------------
    # Amount Validation
    # -----------------------------
    amount = invoice.get("amount")

    if amount is None:
        errors.append("Amount is missing")

    elif amount > CREDIT_LIMIT:
        errors.append("Amount exceeds credit limit")

    # -----------------------------
    # Currency Validation
    # -----------------------------
    currency = invoice.get("currency")

    if currency not in ALLOWED_CURRENCIES:
        errors.append("Unsupported currency")

    # -----------------------------
    # Due Date Validation
    # -----------------------------
    due_date = invoice.get("due_date")

    if not due_date:
        errors.append("Due date is missing")

    else:
        parsed_date = None

        formats = [
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d-%m-%Y",
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(due_date, fmt)
                break
            except ValueError:
                continue

        if not parsed_date:
            errors.append("Invalid due date format")

        else:
            today = datetime.today()

            if parsed_date.date() <= today.date():
                errors.append("Due date must be in the future")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }