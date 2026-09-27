from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import hashlib
from pydantic import BaseModel
from datetime import datetime

from app.db.database import get_db
from app.db.models import (
    Invoice, Vendor, PurchaseOrder, InvoiceCheck, RiskReport, AuditLog, User,
    InvoiceStatus
)
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
from app.services.verification_agent import VerificationAgent
from app.api.auth import get_current_user

router = APIRouter(prefix="/invoices", tags=["invoices"])

class HumanReviewRequest(BaseModel):
    action: str  # "approve", "reject", "flag"
    notes: Optional[str] = None

@router.post("/upload")
async def upload_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ingests invoice PDF/Image -> Deduplication Check -> OCR -> LLM structured extraction -> DB persist -> Tool Agent pipeline.
    """
    file_bytes = await file.read()
    filename = file.filename or "invoice.pdf"
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Step 1: Pre-OCR Exact File Content Deduplication Check
    existing_file = db.query(Invoice).filter(Invoice.file_hash == file_hash).first()
    if existing_file:
        raise HTTPException(
            status_code=409,
            detail=f"Duplicate upload rejected: This exact invoice file already exists (ID: {existing_file.id}, Invoice #: {existing_file.invoice_number or 'Unreadable'}, Status: {existing_file.status})"
        )

    # Step 2: OCR Layer
    ocr_result = OCRService.extract_text_from_file(file_bytes, filename)
    raw_ocr_text = ocr_result["raw_text"]

    # Step 3: LLM Structured Data Extraction
    extracted_json = LLMService.extract_structured_invoice_data(raw_ocr_text)

    # Extract key fields (preserving None if missing)
    invoice_number = extracted_json.get("invoice_number")
    vendor_name = extracted_json.get("vendor_name")
    total_amount = extracted_json.get("total_amount")
    if total_amount is not None:
        try:
            total_amount = float(total_amount)
        except (ValueError, TypeError):
            total_amount = None
    invoice_date = extracted_json.get("invoice_date")

    # Step 4: Vendor Lookup or Registration
    vendor = None
    if vendor_name and vendor_name != "Unknown Vendor":
        vendor = db.query(Vendor).filter(Vendor.name.ilike(f"%{vendor_name}%")).first()
        if not vendor:
            vendor = Vendor(name=vendor_name, gst_number=extracted_json.get("gst_number"))
            db.add(vendor)
            db.commit()
            db.refresh(vendor)

    # Step 5: Post-Extraction (Invoice Number + Vendor) Deduplication Check
    if invoice_number and vendor:
        existing_inv = db.query(Invoice).filter(
            Invoice.invoice_number == invoice_number,
            Invoice.vendor_id == vendor.id
        ).first()
        if existing_inv:
            raise HTTPException(
                status_code=409,
                detail=f"Duplicate invoice rejected: Invoice #{invoice_number} for vendor '{vendor.name}' already exists (ID: {existing_inv.id}, Status: {existing_inv.status})"
            )

    # Step 6: Check for Extraction Failure
    is_extraction_failed = (invoice_number is None or total_amount is None)

    db_invoice = Invoice(
        invoice_number=invoice_number,
        vendor_id=vendor.id if vendor else None,
        file_hash=file_hash,
        raw_ocr_text=raw_ocr_text,
        extracted_json=extracted_json,
        amount=total_amount,
        invoice_date=invoice_date,
        file_name=filename,
        status=InvoiceStatus.EXTRACTION_FAILED.value if is_extraction_failed else InvoiceStatus.PENDING.value
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    if is_extraction_failed:
        audit = AuditLog(
            invoice_id=db_invoice.id,
            actor=current_user.username if current_user else "System",
            action="Extraction Failed",
            notes="Required fields (invoice_number or amount) missing from labeled OCR fields. Needs manual entry."
        )
        db.add(audit)

        report = RiskReport(
            invoice_id=db_invoice.id,
            overall_status="EXTRACTION FAILED - MANUAL ENTRY REQUIRED",
            summary_text=f"Extraction Failed: Required invoice fields ({'Invoice Number' if invoice_number is None else ''} {'Amount' if total_amount is None else ''}) could not be extracted from labeled fields. Manual review and entry required.",
            confidence=0.0
        )
        db.add(report)
        db.commit()

        return {
            "invoice_id": db_invoice.id,
            "invoice_number": db_invoice.invoice_number,
            "vendor": vendor_name or "Unknown Vendor",
            "amount": db_invoice.amount,
            "status": db_invoice.status,
            "extracted_json": db_invoice.extracted_json,
            "verification_result": {
                "overall_status": "EXTRACTION FAILED - MANUAL ENTRY REQUIRED",
                "summary_text": "Extraction Failed: Required fields missing.",
                "confidence": 0.0
            }
        }

    # Initial Audit Log for Successful Extraction
    audit = AuditLog(
        invoice_id=db_invoice.id,
        actor=current_user.username if current_user else "System",
        action="Uploaded invoice file & extracted OCR data",
        notes=f"File: {filename}, extracted Invoice #{invoice_number}, Total Amount: ₹{total_amount:,.2f}"
    )
    db.add(audit)
    db.commit()

    # Step 7: Execute Verification Agent (Tool-Calling Orchestrator Loop)
    agent = VerificationAgent(db)
    agent_output = agent.process_invoice(db_invoice.id)

    db.refresh(db_invoice)

    return {
        "invoice_id": db_invoice.id,
        "invoice_number": db_invoice.invoice_number,
        "vendor": vendor_name,
        "amount": db_invoice.amount,
        "status": db_invoice.status,
        "extracted_json": db_invoice.extracted_json,
        "verification_result": agent_output
    }

@router.get("")
def list_invoices(
    status: Optional[str] = Query(None),
    vendor_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Invoice)
    if status:
        query = query.filter(Invoice.status == status)
    if vendor_id:
        query = query.filter(Invoice.vendor_id == vendor_id)

    invoices = query.order_by(Invoice.created_at.desc()).all()
    
    result = []
    for inv in invoices:
        vendor_name = inv.vendor.name if inv.vendor else "Unknown Vendor"
        risk_summary = inv.risk_report.overall_status if inv.risk_report else "Pending"
        
        # Clean PO reference extraction (ensure literal "REFERENCE" is never displayed)
        raw_po = inv.po.po_number if inv.po else (inv.extracted_json.get("po_reference") if inv.extracted_json else None)
        if raw_po and raw_po.upper() in ["REFERENCE", "ORDER", "NUMBER", "REF"]:
            raw_po = None

        result.append({
            "id": inv.id,
            "invoice_number": inv.invoice_number,
            "vendor_id": inv.vendor_id,
            "vendor_name": vendor_name,
            "po_number": raw_po,
            "po_reference": raw_po,
            "amount": inv.amount,
            "invoice_date": inv.invoice_date,
            "status": inv.status,
            "risk_score": inv.risk_score,
            "risk_summary": risk_summary,
            "file_name": inv.file_name,
            "created_at": str(inv.created_at)
        })
    return result

@router.get("/{invoice_id}")
def get_invoice_details(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    checks = [
        {
            "id": c.id,
            "check_type": c.check_type,
            "result": c.result,
            "details": c.details_json
        }
        for c in inv.checks
    ]

    audit_trail = [
        {
            "id": a.id,
            "actor": a.actor,
            "action": a.action,
            "notes": a.notes,
            "timestamp": str(a.timestamp)
        }
        for a in inv.audit_logs
    ]

    po_details = None
    if inv.po:
        po_details = {
            "id": inv.po.id,
            "po_number": inv.po.po_number,
            "product_name": inv.po.product_name,
            "quantity": inv.po.quantity,
            "unit_price": inv.po.unit_price,
            "total_amount": inv.po.total_amount,
            "line_items": inv.po.line_items
        }

    risk_report = None
    if inv.risk_report:
        risk_report = {
            "overall_status": inv.risk_report.overall_status,
            "summary_text": inv.risk_report.summary_text,
            "confidence": inv.risk_report.confidence,
            "tool_steps": inv.risk_report.tool_steps_json,
            "generated_at": str(inv.risk_report.generated_at)
        }

    raw_po = inv.po.po_number if inv.po else (inv.extracted_json.get("po_reference") if inv.extracted_json else None)
    if raw_po and raw_po.upper() in ["REFERENCE", "ORDER", "NUMBER", "REF"]:
        raw_po = None

    return {
        "id": inv.id,
        "invoice_number": inv.invoice_number,
        "vendor_id": inv.vendor_id,
        "vendor_name": inv.vendor.name if inv.vendor else "Unknown Vendor",
        "vendor_gst": inv.vendor.gst_number if inv.vendor else None,
        "amount": inv.amount,
        "po_reference": raw_po,
        "invoice_date": inv.invoice_date,
        "file_name": inv.file_name,
        "status": inv.status,
        "risk_score": inv.risk_score,
        "raw_ocr_text": inv.raw_ocr_text,
        "extracted_json": inv.extracted_json,
        "po_details": po_details,
        "checks": checks,
        "risk_report": risk_report,
        "audit_logs": audit_trail,
        "created_at": str(inv.created_at)
    }

@router.post("/{invoice_id}/review")
def review_invoice(
    invoice_id: int,
    body: HumanReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    inv = db.query(Invoice).get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    action = body.action.lower()
    if action == "approve":
        inv.status = InvoiceStatus.APPROVED_BY_HUMAN.value
        act_text = "Human Approved Invoice"
    elif action == "reject":
        inv.status = InvoiceStatus.REJECTED.value
        act_text = "Human Rejected Invoice"
    elif action == "flag":
        inv.status = InvoiceStatus.FLAGGED.value
        act_text = "Escalated / Flagged for Management Review"
    else:
        raise HTTPException(status_code=400, detail="Invalid action. Use 'approve', 'reject', or 'flag'.")

    audit = AuditLog(
        invoice_id=inv.id,
        actor=current_user.username if current_user else "Finance Manager",
        action=act_text,
        notes=body.notes or f"Manual action executed by {current_user.username if current_user else 'Finance Manager'}"
    )
    db.add(audit)
    db.commit()
    db.refresh(inv)

    return {"id": inv.id, "status": inv.status, "message": f"Invoice updated to {inv.status}"}

@router.post("/{invoice_id}/rerun")
def rerun_agent(invoice_id: int, db: Session = Depends(get_db)):
    inv = db.query(Invoice).get(invoice_id)
    if not inv:
        raise HTTPException(status_code=404, detail="Invoice not found")

    agent = VerificationAgent(db)
    agent_output = agent.process_invoice(inv.id)
    return agent_output

@router.get("/samples/list")
def list_sample_invoices():
    """Lists pre-generated sample files available for 1-click test upload."""
    samples_dir = "samples"
    if not os.path.exists(samples_dir):
        return []
    files = [f for f in os.listdir(samples_dir) if f.endswith((".pdf", ".png", ".jpg"))]
    
    descriptions = {
        "sample_invoice_INV-4821.pdf": "✓ Original Sample (ABC Tech - INV-4821 - PO-1021 - ₹1,26,000)",
        "invoice_valid_abc_tech.pdf": "✓ Valid Match (ABC Tech - PO-9001 - ₹3,54,000)",
        "invoice_po_mismatch_xyz.pdf": "✗ PO Mismatch (XYZ Logistics - Over PO-9002 amount)",
        "invoice_duplicate_global.pdf": "⚠ Duplicate Invoice No. (INV-4821 Re-upload)",
        "invoice_high_amount_acme.pdf": "⚠ High Deviation (>2.5x Vendor Average)"
    }
    return [
        {
            "filename": filename,
            "description": descriptions.get(filename, filename)
        }
        for filename in files
    ]

@router.post("/process-sample/{sample_name}")
def process_sample_invoice(sample_name: str, db: Session = Depends(get_db)):
    filepath = os.path.join("samples", sample_name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Sample file {sample_name} not found")

    with open(filepath, "rb") as f:
        file_bytes = f.read()

    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Pre-check for existing sample invoice in DB
    existing_sample = db.query(Invoice).filter(
        (Invoice.file_hash == file_hash) | (Invoice.file_name == sample_name)
    ).first()

    if existing_sample:
        # Return existing invoice details without duplicating DB row
        agent_output = {
            "overall_status": existing_sample.risk_report.overall_status if existing_sample.risk_report else "PROCESSED",
            "summary_text": existing_sample.risk_report.summary_text if existing_sample.risk_report else "",
            "confidence": existing_sample.risk_report.confidence if existing_sample.risk_report else 1.0
        }
        return {
            "invoice_id": existing_sample.id,
            "invoice_number": existing_sample.invoice_number,
            "vendor": existing_sample.vendor.name if existing_sample.vendor else "Unknown",
            "amount": existing_sample.amount,
            "status": existing_sample.status,
            "verification_result": agent_output,
            "is_existing": True
        }

    ocr_result = OCRService.extract_text_from_file(file_bytes, sample_name)
    raw_ocr_text = ocr_result["raw_text"]

    extracted_json = LLMService.extract_structured_invoice_data(raw_ocr_text)

    invoice_number = extracted_json.get("invoice_number")
    vendor_name = extracted_json.get("vendor_name")
    total_amount = extracted_json.get("total_amount")
    if total_amount is not None:
        try:
            total_amount = float(total_amount)
        except (ValueError, TypeError):
            total_amount = None
    invoice_date = extracted_json.get("invoice_date")

    vendor = None
    if vendor_name and vendor_name != "Unknown Vendor":
        vendor = db.query(Vendor).filter(Vendor.name.ilike(f"%{vendor_name}%")).first()
        if not vendor:
            vendor = Vendor(name=vendor_name, gst_number=extracted_json.get("gst_number"))
            db.add(vendor)
            db.commit()
            db.refresh(vendor)

    is_extraction_failed = (invoice_number is None or total_amount is None)

    db_invoice = Invoice(
        invoice_number=invoice_number,
        vendor_id=vendor.id if vendor else None,
        file_hash=file_hash,
        raw_ocr_text=raw_ocr_text,
        extracted_json=extracted_json,
        amount=total_amount,
        invoice_date=invoice_date,
        file_name=sample_name,
        status=InvoiceStatus.EXTRACTION_FAILED.value if is_extraction_failed else InvoiceStatus.PENDING.value
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)

    if is_extraction_failed:
        report = RiskReport(
            invoice_id=db_invoice.id,
            overall_status="EXTRACTION FAILED - MANUAL ENTRY REQUIRED",
            summary_text="Extraction Failed: Required invoice fields could not be extracted.",
            confidence=0.0
        )
        db.add(report)
        db.commit()
        return {
            "invoice_id": db_invoice.id,
            "invoice_number": db_invoice.invoice_number,
            "vendor": vendor_name or "Unknown Vendor",
            "amount": db_invoice.amount,
            "status": db_invoice.status,
            "verification_result": {"overall_status": "EXTRACTION FAILED - MANUAL ENTRY REQUIRED"}
        }

    audit = AuditLog(
        invoice_id=db_invoice.id,
        actor="System Demo Preset",
        action="Ingested sample invoice preset",
        notes=f"Processed preset sample {sample_name}"
    )
    db.add(audit)
    db.commit()

    agent = VerificationAgent(db)
    agent_output = agent.process_invoice(db_invoice.id)
    db.refresh(db_invoice)

    return {
        "invoice_id": db_invoice.id,
        "invoice_number": db_invoice.invoice_number,
        "vendor": vendor_name,
        "amount": db_invoice.amount,
        "status": db_invoice.status,
        "verification_result": agent_output
    }
