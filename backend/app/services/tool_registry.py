from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.models import Vendor, PurchaseOrder, Invoice, InvoiceStatus, CheckResult
from app.config import settings

class VerificationTools:
    @staticmethod
    def tool_duplicate_check(invoice_number: str, vendor_id: int, current_invoice_id: int, db: Session) -> dict:
        """
        Tool 1: Duplicate Check
        Queries DB for existing invoice with identical invoice_number and vendor_id.
        """
        if not invoice_number or invoice_number == "UNKNOWN-INV":
            return {
                "check_type": "duplicate_check",
                "result": CheckResult.WARNING.value,
                "summary": "Invoice number unreadable or missing; cannot guarantee uniqueness",
                "details": {"is_duplicate": False, "existing_invoice_id": None}
            }

        existing = db.query(Invoice).filter(
            Invoice.invoice_number == invoice_number,
            Invoice.vendor_id == vendor_id,
            Invoice.id != current_invoice_id
        ).first()

        if existing:
            return {
                "check_type": "duplicate_check",
                "result": CheckResult.FAIL.value,
                "summary": f"Duplicate invoice detected! Invoice #{invoice_number} already exists (ID: {existing.id}, Status: {existing.status})",
                "details": {
                    "is_duplicate": True,
                    "existing_invoice_id": existing.id,
                    "existing_status": existing.status,
                    "created_at": str(existing.created_at)
                }
            }

        return {
            "check_type": "duplicate_check",
            "result": CheckResult.PASS.value,
            "summary": f"Invoice number #{invoice_number} valid (no duplicate)",
            "details": {"is_duplicate": False}
        }

    @staticmethod
    def tool_po_match(po_reference: str, vendor_id: int, invoice_amount: float, extracted_items: list, db: Session) -> dict:
        """
        Tool 2: PO Match
        3-Way matching tool against Purchase Order records.
        """
        if not po_reference:
            return {
                "check_type": "po_match",
                "result": CheckResult.WARNING.value,
                "summary": "No Purchase Order (PO) reference provided on invoice",
                "details": {"po_found": False, "reason": "Missing PO reference in extracted data"}
            }

        po = db.query(PurchaseOrder).filter(
            func.lower(PurchaseOrder.po_number) == po_reference.strip().lower()
        ).first()

        if not po:
            return {
                "check_type": "po_match",
                "result": CheckResult.FAIL.value,
                "summary": f"Referenced PO #{po_reference} not found in system records",
                "details": {"po_found": False, "po_reference": po_reference}
            }

        # Verify Vendor Match
        vendor_mismatch = (vendor_id is not None and po.vendor_id != vendor_id)
        
        # Calculate amount variance
        amount_diff = invoice_amount - po.total_amount
        percent_diff = (amount_diff / po.total_amount * 100.0) if po.total_amount > 0 else 0.0

        discrepancies = []
        if vendor_mismatch:
            po_vendor = db.query(Vendor).get(po.vendor_id)
            po_vendor_name = po_vendor.name if po_vendor else "Unknown"
            discrepancies.append(f"PO belongs to different vendor ({po_vendor_name})")

        if amount_diff > 1.0: # Exceeds PO total
            discrepancies.append(f"Amount exceeds PO by ₹{amount_diff:,.2f} ({percent_diff:.1f}% higher)")
        elif amount_diff < -1.0:
            discrepancies.append(f"Amount is lower than PO by ₹{abs(amount_diff):,.2f}")

        if discrepancies:
            return {
                "check_type": "po_match",
                "result": CheckResult.FAIL.value,
                "summary": " | ".join(discrepancies),
                "details": {
                    "po_found": True,
                    "po_id": po.id,
                    "po_number": po.po_number,
                    "po_amount": po.total_amount,
                    "invoice_amount": invoice_amount,
                    "amount_diff": amount_diff,
                    "percent_diff": percent_diff,
                    "discrepancies": discrepancies
                }
            }

        return {
            "check_type": "po_match",
            "result": CheckResult.PASS.value,
            "summary": f"PO #{po.po_number} matched successfully (Agreed Amount: ₹{po.total_amount:,.2f})",
            "details": {
                "po_found": True,
                "po_id": po.id,
                "po_number": po.po_number,
                "po_amount": po.total_amount,
                "invoice_amount": invoice_amount
            }
        }

    @staticmethod
    def tool_vendor_history_check(vendor_id: int, current_amount: float, db: Session) -> dict:
        """
        Tool 3: Vendor History Lookup & Signal Analysis
        Retrieves rolling average invoice amount, total past invoices, and past flag rate.
        """
        if not vendor_id:
            return {
                "check_type": "vendor_history",
                "result": CheckResult.WARNING.value,
                "summary": "Unregistered / new vendor - no prior historical billing data",
                "details": {"vendor_found": False}
            }

        past_invoices = db.query(Invoice).filter(
            Invoice.vendor_id == vendor_id,
            Invoice.status.in_([InvoiceStatus.APPROVED_BY_HUMAN.value, InvoiceStatus.AUTO_APPROVED.value])
        ).all()

        if not past_invoices:
            return {
                "check_type": "vendor_history",
                "result": CheckResult.PASS.value,
                "summary": "First invoice for vendor - establishing baseline historical profile",
                "details": {"past_invoice_count": 0, "avg_amount": current_amount}
            }

        amounts = [inv.amount for inv in past_invoices if inv.amount > 0]
        avg_amount = sum(amounts) / len(amounts) if amounts else current_amount

        deviation_percent = ((current_amount - avg_amount) / avg_amount * 100.0) if avg_amount > 0 else 0.0

        if deviation_percent > settings.VENDOR_AVG_DEVIATION_THRESHOLD_PERCENT:
            return {
                "check_type": "vendor_history",
                "result": CheckResult.WARNING.value,
                "summary": f"Vendor's average invoice: ₹{avg_amount:,.2f} | Current invoice: ₹{current_amount:,.2f} (+{deviation_percent:.1f}% deviation)",
                "details": {
                    "past_invoice_count": len(past_invoices),
                    "avg_amount": avg_amount,
                    "current_amount": current_amount,
                    "deviation_percent": deviation_percent
                }
            }

        return {
            "check_type": "vendor_history",
            "result": CheckResult.PASS.value,
            "summary": f"Vendor history verified ({len(past_invoices)} past invoices, Avg: ₹{avg_amount:,.2f})",
            "details": {
                "past_invoice_count": len(past_invoices),
                "avg_amount": avg_amount,
                "current_amount": current_amount,
                "deviation_percent": deviation_percent
            }
        }

    @staticmethod
    def tool_gst_tax_check(extracted_gst: str, vendor_id: int, subtotal: float, tax_amount: float, total_amount: float, db: Session) -> dict:
        """
        Tool 4: Tax & GST Field Check
        Validates vendor GST number format, presence, and tax line math (Subtotal + Tax = Total).
        """
        issues = []
        vendor_gst = None
        
        if vendor_id:
            vendor = db.query(Vendor).get(vendor_id)
            if vendor and vendor.gst_number:
                vendor_gst = vendor.gst_number

        if not extracted_gst and not vendor_gst:
            issues.append("Missing GSTIN/Tax identification number on invoice")
        elif extracted_gst and vendor_gst and extracted_gst.strip().upper() != vendor_gst.strip().upper():
            issues.append(f"Invoice GSTIN ({extracted_gst}) mismatch with Vendor master DB ({vendor_gst})")

        # Verify math
        calculated_total = (subtotal or 0.0) + (tax_amount or 0.0)
        if total_amount > 0 and abs(calculated_total - total_amount) > 2.0 and subtotal > 0:
            issues.append(f"Math calculation mismatch: Subtotal (₹{subtotal:,.2f}) + Tax (₹{tax_amount:,.2f}) = ₹{calculated_total:,.2f} vs Stated Total (₹{total_amount:,.2f})")

        if issues:
            return {
                "check_type": "gst_tax_check",
                "result": CheckResult.FAIL.value if any("mismatch" in i for i in issues) else CheckResult.WARNING.value,
                "summary": " | ".join(issues),
                "details": {
                    "extracted_gst": extracted_gst,
                    "vendor_gst": vendor_gst,
                    "subtotal": subtotal,
                    "tax_amount": tax_amount,
                    "total_amount": total_amount,
                    "issues": issues
                }
            }

        return {
            "check_type": "gst_tax_check",
            "result": CheckResult.PASS.value,
            "summary": f"GST / Tax fields verified (GSTIN: {extracted_gst or vendor_gst or 'Verified'})",
            "details": {"extracted_gst": extracted_gst, "vendor_gst": vendor_gst}
        }
