import json
import re
import httpx
from app.config import settings

class LLMService:
    @staticmethod
    def extract_structured_invoice_data(raw_text: str) -> dict:
        """
        Uses LLM (or regex fallback) to convert unstructured OCR raw text into structured JSON.
        Returns dictionary with:
        vendor_name, gst_number, invoice_number, po_reference, invoice_date, subtotal, tax_amount, total_amount, line_items
        """
        # If Gemini API key is available, call Gemini API
        if settings.GEMINI_API_KEY:
            try:
                return LLMService._extract_via_gemini(raw_text)
            except Exception as e:
                print(f"[LLMService] Gemini extraction failed: {e}. Falling back to deterministic parser.")
        
        # If OpenAI API key is available, call OpenAI API
        if settings.OPENAI_API_KEY:
            try:
                return LLMService._extract_via_openai(raw_text)
            except Exception as e:
                print(f"[LLMService] OpenAI extraction failed: {e}. Falling back to deterministic parser.")
        
        # Fallback to intelligent rule-based / regex parser
        return LLMService._deterministic_extraction_fallback(raw_text)

    @staticmethod
    def _deterministic_extraction_fallback(raw_text: str) -> dict:
        """
        Parse raw text strictly from labeled fields to prevent mis-extraction from narrative text or address blocks.
        """
        data = {
            "vendor_name": None,
            "gst_number": None,
            "invoice_number": None,
            "po_reference": None,
            "invoice_date": None,
            "subtotal": None,
            "tax_amount": None,
            "total_amount": None,
            "line_items": []
        }

        if not raw_text or not raw_text.strip():
            return data

        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
        blacklisted_words = {"DATE", "NO", "NUMBER", "NUM", "DETAILS", "PLOT", "TO", "FROM", "REF", "REFERENCE", "INVOICE", "SUMMARY", "ITEM", "PAGE", "TERMS", "ORDER", "DETAILS"}

        # 1. Invoice Number (Anchored strictly on labeled fields like "Invoice #:", "Invoice No:", "Inv #:")
        inv_match = re.search(r'(?:invoice|inv)\s*(?:no|number|num|\#|code|id)?[ \t]*[:#=][ \t]*([A-Z0-9-]+)', raw_text, re.IGNORECASE)
        if inv_match:
            cand = inv_match.group(1).strip().upper()
            if cand not in blacklisted_words and len(cand) >= 3:
                data["invoice_number"] = cand

        # 2. PO Reference (Anchored strictly on labeled PO fields e.g. "PO Reference: PO-1021", "PO #: PO-9001")
        po_matches = re.finditer(r'(?:po\s*(?:reference|ref|no|number|\#)?|purchase\s*order\s*(?:reference|ref|no|number|\#)?)[ \t]*[:#=][ \t]*([A-Z0-9-]+)', raw_text, re.IGNORECASE)
        for pm in po_matches:
            cand = pm.group(1).strip().upper()
            if cand not in blacklisted_words and cand != "REFERENCE" and cand != "ORDER":
                data["po_reference"] = cand
                break

        # 3. GST Number
        gst_match = re.search(r'\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b', raw_text)
        if gst_match:
            data["gst_number"] = gst_match.group(0)

        # 4. Invoice Date
        date_match = re.search(r'(?:invoice\s*date|date)[ \t]*[:#=][ \t]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})', raw_text, re.IGNORECASE)
        if date_match:
            data["invoice_date"] = date_match.group(1)
        else:
            generic_date = re.search(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}-\d{2}-\d{2})\b', raw_text)
            if generic_date:
                data["invoice_date"] = generic_date.group(1)

        # 5. Amounts (Total, Subtotal, Tax) - Restrict delimiters to same-line whitespace only [ \t:=₹$]+
        total_match = re.search(
            r'\b(?:grand\s*total\s*payable|total\s*amount\s*payable|grand\s*total|total\s*amount|total\s*payable|amount\s*payable|amount\s*due|net\s*total|total\s*due|total)\b[ \t:=₹$]+([0-9,]+(?:\.[0-9]+)?)',
            raw_text, re.IGNORECASE
        )
        if total_match:
            try:
                val = float(total_match.group(1).replace(',', ''))
                if val > 0:
                    data["total_amount"] = val
            except ValueError:
                pass

        subtotal_match = re.search(
            r'\b(?:subtotal|sub-total|net\s*amount)\b[ \t:=₹$]+([0-9,]+(?:\.[0-9]+)?)',
            raw_text, re.IGNORECASE
        )
        if subtotal_match:
            try:
                val = float(subtotal_match.group(1).replace(',', ''))
                if val > 0:
                    data["subtotal"] = val
            except ValueError:
                pass

        tax_match = re.search(
            r'\b(?:gst\s*\(?\d*%\)?|tax|vat)\b[ \t:=₹$]+([0-9,]+(?:\.[0-9]+)?)',
            raw_text, re.IGNORECASE
        )
        if tax_match:
            try:
                val = float(tax_match.group(1).replace(',', ''))
                data["tax_amount"] = val
            except ValueError:
                pass

        # 6. Vendor Name extraction
        vendor_label_match = re.search(r'(?:vendor|supplier|seller|bill\s*from|from)[ \t]*[:=][ \t]*([^\n,]+)', raw_text, re.IGNORECASE)
        if vendor_label_match:
            v_cand = vendor_label_match.group(1).strip()
            if not any(kw in v_cand.lower() for kw in ["plot", "street", "road", "tel", "phone", "gstin"]):
                data["vendor_name"] = v_cand

        if not data["vendor_name"]:
            # Check top header company name
            for line in lines[:4]:
                clean_line = line.replace("=", "").strip()
                if any(clean_line.lower().startswith(skip) for skip in ["plot", "address", "road", "hitech", "tel", "gstin", "date", "invoice", "page", "bill to", "contact"]):
                    continue
                if len(clean_line) > 3 and not re.match(r'^\d+$', clean_line):
                    data["vendor_name"] = clean_line
                    break

        # 7. Line items parsing
        line_item_matches = re.findall(r'([A-Za-z0-9\s-]+?)\s+(\d+)\s+x?\s*[₹$]?\s*([0-9,]+\.?[0-9]*)\s+[₹$]?\s*([0-9,]+\.?[0-9]*)', raw_text)
        for item in line_item_matches:
            try:
                data["line_items"].append({
                    "description": item[0].strip(),
                    "quantity": float(item[1]),
                    "unit_price": float(item[2].replace(',', '')),
                    "total": float(item[3].replace(',', ''))
                })
            except ValueError:
                pass

        if data["total_amount"] is None and data["subtotal"] is not None and data["tax_amount"] is not None:
            data["total_amount"] = data["subtotal"] + data["tax_amount"]

        return data

    @staticmethod
    def _extract_via_gemini(raw_text: str) -> dict:
        """Call Google Gemini API for JSON extraction with strict label grounding prompt."""
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        prompt = f"""Extract structured JSON invoice data from the following OCR text.
CRITICAL INSTRUCTION: Extract fields ONLY where a clear label precedes the value (e.g. 'Invoice #:', 'Invoice Date:', 'PO Reference:', 'PO #:', 'Vendor:' or a company name in the top header block).
Do NOT extract from narrative paragraphs, notes, address blocks (such as 'Plot ...'), terms-and-conditions text, or random body words.
If a field cannot be confidently identified from a labeled source, return null for that field — never guess or return the nearest word or placeholder string.

Return ONLY a valid JSON object matching this schema:
{{
  "vendor_name": "string or null",
  "gst_number": "string or null",
  "invoice_number": "string or null",
  "po_reference": "string or null",
  "invoice_date": "YYYY-MM-DD or string or null",
  "subtotal": float or null,
  "tax_amount": float or null,
  "total_amount": float or null,
  "line_items": [
     {{"description": "string", "quantity": float, "unit_price": float, "total": float}}
  ]
}}

OCR Raw Text:
{raw_text}
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"response_mime_type": "application/json"}
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            res_data = resp.json()
            text_resp = res_data["candidates"][0]["content"]["parts"][0]["text"]
            return json.loads(text_resp)

    @staticmethod
    def _extract_via_openai(raw_text: str) -> dict:
        """Call OpenAI API for JSON extraction with strict label grounding prompt."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"""Extract structured JSON invoice data from the following OCR text.
CRITICAL INSTRUCTION: Extract fields ONLY where a clear label precedes the value (e.g. 'Invoice #:', 'Invoice Date:', 'PO Reference:', 'PO #:', 'Vendor:' or a company name in the top header block).
Do NOT extract from narrative paragraphs, notes, address blocks (such as 'Plot ...'), terms-and-conditions text, or random body words.
If a field cannot be confidently identified from a labeled source, return null for that field — never guess or return the nearest word or placeholder string.

Extract fields: vendor_name, gst_number, invoice_number, po_reference, invoice_date, subtotal, tax_amount, total_amount, line_items.
Return null for missing or unconfident fields.

OCR Raw Text:
{raw_text}"""
        payload = {
            "model": "gpt-4o-mini",
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You extract structured invoice JSON strictly from labeled fields."},
                {"role": "user", "content": prompt}
            ]
        }
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)

    @staticmethod
    def synthesize_agent_verdict(invoice_no: str, vendor_name: str, checks: list, confidence: float) -> dict:
        """
        Synthesizes a human-readable risk summary string and overall status verdict from check results.
        """
        has_fail = any(c["result"] == "fail" for c in checks)
        has_warning = any(c["result"] == "warning" for c in checks)

        if has_fail:
            overall_status = "HUMAN REVIEW REQUIRED"
        elif has_warning:
            overall_status = "NEEDS FINANCE ATTENTION"
        else:
            overall_status = "AUTO APPROVED RECOMMENDATION"

        lines = [
            f"Invoice: {invoice_no or 'Unreadable'}",
            f"Vendor: {vendor_name or 'Unknown Vendor'}",
            ""
        ]

        for check in checks:
            result_symbol = "✓" if check["result"] == "pass" else ("✗" if check["result"] == "fail" else "⚠")
            lines.append(f"{result_symbol} {check['summary']}")

        lines.append("")
        lines.append(f"Status: {overall_status}")
        lines.append(f"Confidence: {confidence:.2f}")

        summary_text = "\n".join(lines)

        return {
            "overall_status": overall_status,
            "summary_text": summary_text,
            "confidence": confidence
        }
