import json
import os
import re
import base64
import time
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google import genai
from pydantic import BaseModel, ValidationError

BASE_DIR = Path(__file__).resolve().parent
ROOT_DIR = BASE_DIR.parent
load_dotenv(BASE_DIR / ".env")


# -----------------------------
# Pydantic Schemas
# -----------------------------

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class InvoiceData(BaseModel):
    vendor: Optional[str] = None
    invoice_no: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    due_date: Optional[str] = None
    line_items: List[LineItem] = []


# -----------------------------
# Gemini Config
# -----------------------------

API_KEY = os.getenv("GENAI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
if not API_KEY:
    raise ValueError("Missing GENAI_API_KEY in day2/components/.env")
client = genai.Client(api_key=API_KEY)


# -----------------------------
# Load Prompt
# -----------------------------

PROMPT_PATH = ROOT_DIR / "prompts" / "invoice_extract.txt"

if not PROMPT_PATH.exists():
    raise FileNotFoundError(f"Prompt file not found: {PROMPT_PATH}")

BASE_PROMPT = PROMPT_PATH.read_text(encoding="utf-8")


# -----------------------------
# Helpers
# -----------------------------

def extract_json(text: str) -> dict:
    """
    Extract JSON from LLM response safely.
    """

    text = text.strip()

    # remove markdown code fences
    text = re.sub(r"```json", "", text)
    text = re.sub(r"```", "", text)

    match = re.search(r"\{.*\}", text, re.DOTALL)

    if not match:
        raise ValueError("No JSON found in LLM response")

    return json.loads(match.group())


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


# -----------------------------
# Main Function
# -----------------------------

def extract_invoice_data_from_base64(b64_pdf: str) -> InvoiceData:
    """
    Takes invoice PDF path -> sends PDF as base64 inline_data -> validates schema.
    """

    model_candidates = []
    for name in [
        MODEL_NAME,
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-2.5-flash",
    ]:
        if name and name not in model_candidates:
            model_candidates.append(name)

    last_error = None
    response = None
    for model_name in model_candidates:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    {
                        "parts": [
                            {"text": BASE_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": "application/pdf",
                                    "data": b64_pdf,
                                }
                            },
                        ]
                    }
                ],
            )
            break
        except Exception as e:
            last_error = e
            continue

    if response is None:
        raise RuntimeError(f"All models failed. Last error: {last_error}")

    raw_output = response.text

    parsed_json = extract_json(raw_output)

    validated = InvoiceData.model_validate(parsed_json)

    return validated


# -----------------------------
# Test Runner
# -----------------------------

if __name__ == "__main__":
    pdf_dir = BASE_DIR / "invoice_pdf"
    pdf_paths = sorted(pdf_dir.glob("*.pdf"))

    if not pdf_paths:
        raise FileNotFoundError(f"No PDFs found in: {pdf_dir}")

    base64_output_dir = BASE_DIR / "json" / "base64_pdf"
    base64_output_dir.mkdir(parents=True, exist_ok=True)
    output_json_dir = BASE_DIR / "json" / "llm_extracted_json_data"
    output_json_dir.mkdir(parents=True, exist_ok=True)

    # clean previous extracted json files
    for old_file in output_json_dir.glob("*.json"):
        old_file.unlink()
    print(f"Cleaned old JSON files in: {output_json_dir}")

    # Step 1: store base64 for each PDF
    for idx, pdf_path in enumerate(pdf_paths, start=1):
        b64_text = base64.b64encode(pdf_path.read_bytes()).decode("utf-8")
        b64_path = base64_output_dir / f"{pdf_path.stem}.base64.txt"
        b64_path.write_text(b64_text, encoding="utf-8")
        print(f"Saved base64: {b64_path}")

    # Step 2: call Gemini from stored base64 files
    base64_files = sorted(base64_output_dir.glob("*.base64.txt"))
    combined_results = []
    for idx, b64_file in enumerate(base64_files, start=1):
        print(f"\n========== BASE64 {idx}: {b64_file.name} ==========\n")
        try:
            b64_text = b64_file.read_text(encoding="utf-8").strip()
            result = extract_invoice_data_from_base64(b64_text)
            print(result.model_dump_json(indent=2))

            source_pdf_name = b64_file.name.replace(".base64.txt", ".pdf")
            record = {
                "source_pdf": source_pdf_name,
                "model": MODEL_NAME,
                "parsed_data": result.model_dump(),
            }
            safe_name = sanitize_filename(b64_file.stem.replace(".base64", ""))
            out_path = output_json_dir / f"{safe_name}.json"
            out_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
            print(f"Saved extracted JSON: {out_path}")
            combined_results.append(record)

            time.sleep(float(os.getenv("GEMINI_BETWEEN_FILE_DELAY", "2")))
        except ValidationError as ve:
            print("Schema Validation Error:")
            print(ve)
        except Exception as e:
            print("Error:")
            print(e)
            msg = str(e)
            if "429" in msg or "RESOURCE_EXHAUSTED" in msg:
                time.sleep(float(os.getenv("GEMINI_RETRY_DELAY_ON_429", "60")))

    if combined_results:
        combined_path = output_json_dir / f"all_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        combined_path.write_text(json.dumps(combined_results, indent=2), encoding="utf-8")
        print(f"\nSaved combined results: {combined_path}")
