from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.db.database import get_db
from app.db.models import Vendor, Invoice, PurchaseOrder, InvoiceStatus, CheckResult

router = APIRouter(prefix="/vendors", tags=["vendors"])

@router.get("")
def list_vendors(db: Session = Depends(get_db)):
    vendors = db.query(Vendor).all()
    result = []
    for v in vendors:
        inv_count = db.query(Invoice).filter(Invoice.vendor_id == v.id).count()
        flagged_count = db.query(Invoice).filter(
            Invoice.vendor_id == v.id, 
            Invoice.status.in_([InvoiceStatus.FLAGGED.value, InvoiceStatus.REJECTED.value])
        ).count()
        total_spent = db.query(func.sum(Invoice.amount)).filter(
            Invoice.vendor_id == v.id,
            Invoice.status.in_([InvoiceStatus.APPROVED_BY_HUMAN.value, InvoiceStatus.AUTO_APPROVED.value])
        ).scalar() or 0.0

        result.append({
            "id": v.id,
            "name": v.name,
            "gst_number": v.gst_number,
            "invoice_count": inv_count,
            "flagged_count": flagged_count,
            "total_spent": total_spent,
            "created_at": str(v.created_at)
        })
    return result

@router.get("/{vendor_id}/profile")
def get_vendor_risk_profile(vendor_id: int, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).get(vendor_id)
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    invoices = db.query(Invoice).filter(Invoice.vendor_id == vendor.id).all()
    pos = db.query(PurchaseOrder).filter(PurchaseOrder.vendor_id == vendor.id).all()

    total_invoices = len(invoices)
    approved_invoices = [i for i in invoices if i.status in [InvoiceStatus.APPROVED_BY_HUMAN.value, InvoiceStatus.AUTO_APPROVED.value]]
    flagged_invoices = [i for i in invoices if i.status == InvoiceStatus.FLAGGED.value]
    rejected_invoices = [i for i in invoices if i.status == InvoiceStatus.REJECTED.value]

    amounts = [i.amount for i in approved_invoices if i.amount > 0]
    avg_invoice_amount = sum(amounts) / len(amounts) if amounts else 0.0
    total_spent = sum(amounts)

    mismatch_rate = (len(flagged_invoices) + len(rejected_invoices)) / total_invoices * 100.0 if total_invoices > 0 else 0.0

    recent_invoices = [
        {
            "id": i.id,
            "invoice_number": i.invoice_number,
            "amount": i.amount,
            "status": i.status,
            "date": i.invoice_date,
            "created_at": str(i.created_at)
        }
        for i in sorted(invoices, key=lambda x: x.created_at, reverse=True)[:10]
    ]

    return {
        "vendor_id": vendor.id,
        "name": vendor.name,
        "gst_number": vendor.gst_number,
        "metrics": {
            "total_invoices": total_invoices,
            "approved_count": len(approved_invoices),
            "flagged_count": len(flagged_invoices),
            "rejected_count": len(rejected_invoices),
            "avg_invoice_amount": avg_invoice_amount,
            "total_spent": total_spent,
            "mismatch_rate_percent": round(mismatch_rate, 1),
            "total_pos_count": len(pos)
        },
        "recent_invoices": recent_invoices
    }
