from datetime import datetime, timedelta

from components.validator import validate_invoice


future_date = (datetime.today() + timedelta(days=10)).strftime("%Y-%m-%d")
past_date = (datetime.today() - timedelta(days=5)).strftime("%Y-%m-%d")


def test_valid_invoice():

    invoice = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "USD",
        "due_date": future_date,
    }

    result = validate_invoice(invoice)

    assert result["valid"] is True
    assert result["errors"] == []


def test_invalid_vendor():

    invoice = {
        "vendor": "Fake Vendor",
        "amount": 5000,
        "currency": "USD",
        "due_date": future_date,
    }

    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert "Vendor is not approved" in result["errors"]


def test_credit_limit_exceeded():

    invoice = {
        "vendor": "ACME Corp",
        "amount": 50000,
        "currency": "USD",
        "due_date": future_date,
    }

    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert "Amount exceeds credit limit" in result["errors"]


def test_invalid_currency():

    invoice = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "EUR",
        "due_date": future_date,
    }

    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert "Unsupported currency" in result["errors"]


def test_past_due_date():

    invoice = {
        "vendor": "ACME Corp",
        "amount": 5000,
        "currency": "USD",
        "due_date": past_date,
    }

    result = validate_invoice(invoice)

    assert result["valid"] is False
    assert "Due date must be in the future" in result["errors"]