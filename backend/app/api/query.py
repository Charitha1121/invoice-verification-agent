from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
import re

from app.db.database import get_db
from app.db.models import Invoice, Vendor, PurchaseOrder, InvoiceStatus, RiskReport

router = APIRouter(prefix="/query", tags=["query"])

class QueryRequest(BaseModel):
    query: str

@router.post("")
def natural_language_query(payload: QueryRequest, db: Session = Depends(get_db)):
    q = payload.query.lower().strip()
    results = []

    # Simple intent parsing engine
    invoices_q = db.query(Invoice)

    if "flagged" in q or "review" in q or "mismatch" in q:
        invoices_q = invoices_q.filter(Invoice.status == InvoiceStatus.FLAGGED.value)
    elif "approved" in q:
        invoices_q = invoices_q.filter(Invoice.status.in_([InvoiceStatus.APPROVED_BY_HUMAN.value, InvoiceStatus.AUTO_APPROVED.value]))
    elif "rejected" in q:
        invoices_q = invoices_q.filter(Invoice.status == InvoiceStatus.REJECTED.value)

    # Search amount filters
    amount_match = re.search(r'(?:over|greater than|above|>)\s*₹?\s*([0-9,]+)', q)
    if amount_match:
        val = float(amount_match.group(1).replace(',', ''))
        invoices_q = invoices_q.filter(Invoice.amount > val)

    invoices = invoices_q.order_by(Invoice.created_at.desc()).all()

    for inv in invoices:
        vname = inv.vendor.name if inv.vendor else "Unknown Vendor"
        risk_summary = inv.risk_report.overall_status if inv.risk_report else "Pending"
        
        # Check text match if specific keyword searched
        summary_text = inv.risk_report.summary_text if inv.risk_report else ""
        if "po" in q and "po" not in summary_text.lower() and "po" not in str(inv.extracted_json).lower():
            continue

        results.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor_name": vname,
            "amount": inv.amount,
            "status": inv.status,
            "risk_summary": risk_summary,
            "summary_text": summary_text,
            "invoice_date": inv.invoice_date,
            "created_at": str(inv.created_at)
        })

    return {
        "query": payload.query,
        "matched_count": len(results),
        "results": results
    }
