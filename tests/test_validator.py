from datetime import date, timedelta
import importlib.util
from pathlib import Path

_VALIDATOR_PATH = Path(__file__).resolve().parents[1] / "day2" / "components" / "validator.py"
_SPEC = importlib.util.spec_from_file_location("validator", _VALIDATOR_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise ImportError(f"Unable to load validator module from {_VALIDATOR_PATH}")
_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
validate_invoice = _MODULE.validate_invoice


def _future_date(days: int = 5) -> str:
    return (date.today() + timedelta(days=days)).strftime("%Y-%m-%d")


def _past_date(days: int = 1) -> str:
    return (date.today() - timedelta(days=days)).strftime("%Y-%m-%d")


def test_validate_invoice_valid_payload():
    invoice = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "INR",
        "due_date": _future_date(),
    }

    result = validate_invoice(invoice)

    assert result["valid"] is True
    assert result["errors"] == []


def test_validate_invoice_rejects_unapproved_vendor():
    invoice = {
        "vendor": "Unknown Vendor",
        "amount": 5000,
        "currency": "INR",
        "due_date": _future_date(),
    }

    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert "Vendor is not approved" in result["errors"]


def test_validate_invoice_rejects_amount_limit_and_missing_amount():
    over_limit = {
        "vendor": "ACME Corp",
        "amount": 15000,
        "currency": "INR",
        "due_date": _future_date(),
    }
    missing_amount = {
        "vendor": "ACME Corp",
        "amount": None,
        "currency": "INR",
        "due_date": _future_date(),
    }

    over_limit_result = validate_invoice(over_limit)
    missing_amount_result = validate_invoice(missing_amount)

    assert "Amount exceeds credit limit" in over_limit_result["errors"]
    assert "Amount is missing" in missing_amount_result["errors"]


def test_validate_invoice_rejects_unsupported_currency():
    invoice = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "EUR",
        "due_date": _future_date(),
    }

    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert "Unsupported currency" in result["errors"]


def test_validate_invoice_rejects_missing_due_date_invalid_format_and_past_date():
    missing_due = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "USD",
        "due_date": None,
    }
    bad_format = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "USD",
        "due_date": "2026/05/09",
    }
    past_due = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "USD",
        "due_date": _past_date(),
    }

    missing_result = validate_invoice(missing_due)
    bad_format_result = validate_invoice(bad_format)
    past_due_result = validate_invoice(past_due)

    assert "Due date is missing" in missing_result["errors"]
    assert "Invalid due date format" in bad_format_result["errors"]
    assert "Due date must be in the future" in past_due_result["errors"]
