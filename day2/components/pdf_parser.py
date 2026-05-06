import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from pypdf import PdfReader

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def empty_response() -> Dict[str, Any]:
    return {
        "vendor": None,
        "invoice_no": None,
        "amount": None,
        "currency": None,
        "due_date": None,
        "line_items": [],
    }


def to_float(value: Optional[str]) -> Optional[float]:
    if not value:
        return None
    cleaned = re.sub(r"[^0-9.\-]", "", value)
    if not cleaned:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_text_from_pdf(pdf_path: str) -> str:
    text_parts: List[str] = []
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts)


def find_first(patterns: List[str], text: str, flags: int = re.IGNORECASE) -> Optional[str]:
    for pattern in patterns:
        match = re.search(pattern, text, flags)
        if match:
            value = (match.group(1) or "").strip()
            if value:
                return value
    return None


def extract_line_items(text: str) -> List[Dict[str, Any]]:
    line_items: List[Dict[str, Any]] = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    # Heuristic: lines like "Widget A 2 50.00 100.00"
    item_pattern = re.compile(r"^(.*\D)\s+(\d+(?:\.\d+)?)\s+([0-9,]+(?:\.\d+)?)\s+([0-9,]+(?:\.\d+)?)$")
    for line in lines:
        m = item_pattern.match(line)
        if not m:
            continue
        description = m.group(1).strip()
        qty = to_float(m.group(2))
        price = to_float(m.group(3))
        if description and (qty is not None or price is not None):
            line_items.append(
                {
                    "description": description,
                    "quantity": qty,
                    "price": price,
                }
            )
    return line_items


def parse_invoice_pdf(pdf_path: str) -> Dict[str, Any]:
    try:
        text = extract_text_from_pdf(pdf_path)
        if not text.strip():
            return empty_response()

        vendor = find_first(
            [
                r"Vendor\s*Name\s*[:\-]\s*(.+)",
                r"From\s*[:\-]\s*(.+)",
                r"Bill\s*From\s*[:\-]\s*(.+)",
            ],
            text,
        )
        invoice_no = find_first(
            [
                r"Invoice\s*(?:No|#|Number)\s*[:\-]\s*([A-Za-z0-9\-\/]+)",
                r"Inv\s*(?:No|#)\s*[:\-]\s*([A-Za-z0-9\-\/]+)",
            ],
            text,
        )
        due_date = find_first(
            [
                r"Due\s*Date\s*[:\-]\s*([0-9]{4}-[0-9]{2}-[0-9]{2})",
                r"Due\s*Date\s*[:\-]\s*([0-9]{2}[\/\-][0-9]{2}[\/\-][0-9]{4})",
            ],
            text,
        )
        currency = find_first(
            [
                r"\b(USD|INR|EUR|GBP)\b",
                r"Currency\s*[:\-]\s*([A-Z]{3})",
            ],
            text,
        )
        amount_text = find_first(
            [
                r"Total\s*Amount\s*[:\-]\s*([$€£₹]?\s*[0-9,]+(?:\.[0-9]{1,2})?)",
                r"Grand\s*Total\s*[:\-]\s*([$€£₹]?\s*[0-9,]+(?:\.[0-9]{1,2})?)",
                r"Amount\s*Due\s*[:\-]\s*([$€£₹]?\s*[0-9,]+(?:\.[0-9]{1,2})?)",
            ],
            text,
        )
        amount = to_float(amount_text)
        line_items = extract_line_items(text)

        return {
            "vendor": vendor,
            "invoice_no": invoice_no,
            "amount": amount,
            "currency": currency,
            "due_date": due_date,
            "line_items": line_items,
        }
    except Exception as e:
        print(f"PDF parse error for {pdf_path}: {e}")
        return empty_response()


def test_invoices(pdf_paths: List[str]) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for path in pdf_paths:
        print(f"Processing: {path}")
        results.append(parse_invoice_pdf(path))
    return results


def process_pdf_folder_and_store_results(pdf_folder: str, output_dir: str) -> str:
    if not os.path.isdir(pdf_folder):
        raise FileNotFoundError(f"PDF folder not found: {pdf_folder}")

    pdf_paths = sorted(
        [
            os.path.join(pdf_folder, file_name)
            for file_name in os.listdir(pdf_folder)
            if file_name.lower().endswith(".pdf")
        ]
    )
    if not pdf_paths:
        raise FileNotFoundError(f"No PDF files found in: {pdf_folder}")

    parsed = test_invoices(pdf_paths)
    payload = []
    for path, data in zip(pdf_paths, parsed):
        payload.append(
            {
                "file_name": os.path.basename(path),
                "file_path": path,
                "parsed_data": data,
            }
        )

    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(
        output_dir,
        f"parsed_invoices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
    )
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return out_file


if __name__ == "__main__":
    pdf_folder = os.path.join(BASE_DIR, "invoice_pdf")
    output_dir = os.path.join(BASE_DIR, "json")
    saved_file = process_pdf_folder_and_store_results(pdf_folder, output_dir)
    print(f"Saved parsed results to: {saved_file}")
