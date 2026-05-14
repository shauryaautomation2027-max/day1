# engine/components.py

def email_reader(params):

    return {
        "status": "success",
        "emails_found": 5
    }


def pdf_parser(params):

    return {
        "status": "success",
        "pages": 10
    }


def llm_extractor(params):

    return {
        "status": "success",
        "fields_extracted": [
            "invoice_number",
            "amount"
        ]
    }


def validator(params):

    return {
        "status": "success",
        "validated": True
    }