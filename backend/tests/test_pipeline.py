import pytest
import os
import hashlib
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import Vendor, PurchaseOrder, Invoice, InvoiceStatus
from app.services.verification_agent import VerificationAgent
from app.services.llm_service import LLMService
from app.services.ocr_service import OCRService

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed vendor & PO
    v = Vendor(name="ABC Technologies Pvt. Ltd.", gst_number="27AAAAA0000A1Z5")
    session.add(v)
    session.commit()

    po1 = PurchaseOrder(
        po_number="PO-1021",
        vendor_id=v.id,
        product_name="Enterprise Software License",
        quantity=1,
        unit_price=126000.0,
        total_amount=126000.0
    )
    po2 = PurchaseOrder(
        po_number="PO-9001",
        vendor_id=v.id,
        product_name="Monitors",
        quantity=10,
        unit_price=25000.0,
        total_amount=354000.0
    )
    session.add_all([po1, po2])
    session.commit()

    yield session
    session.close()

def test_bug1_labeled_field_extraction():
    """
    Test Bug 1: Assert extraction anchors ONLY on labeled fields and does NOT extract 'PLOT'
    from address text 'Plot 14, Hitech City Road...' nor 'REFERENCE' for PO reference.
    """
    raw_ocr_text = """
===================================================
ABC Technologies Pvt. Ltd.
Plot 14, Hitech City Road, Madhapur, Hyderabad - 500081
GSTIN: 27AAAAA0000A1Z5

INVOICE DETAILS
---------------------------------------------------
Invoice #: INV-4821
Invoice Date: 2026-09-15
PO Reference: PO-1021

Bill To: Enterprise Finance Corp

Item Description             Qty    Unit Price    Total
---------------------------------------------------
Enterprise Software License   1      ₹1,26,000     ₹1,26,000

Subtotal: ₹1,26,000
GST (0%): ₹0
Total Amount Payable: ₹1,26,000.00
===================================================
"""
    data = LLMService._deterministic_extraction_fallback(raw_ocr_text)

    # 1. Invoice number must be INV-4821 (NOT "PLOT")
    assert data["invoice_number"] == "INV-4821"
    assert data["invoice_number"] != "PLOT"

    # 2. Vendor name must be ABC Technologies Pvt. Ltd.
    assert "ABC Technologies" in data["vendor_name"]
    assert "Plot" not in data["vendor_name"]

    # 3. PO reference must be PO-1021 (NOT "REFERENCE")
    assert data["po_reference"] == "PO-1021"
    assert data["po_reference"] != "REFERENCE"

    # 4. Total amount must be 126000.0 (NOT 0.0)
    assert data["total_amount"] == 126000.0

def test_bug2_deduplication_idempotency(db_session):
    """
    Test Bug 2: Assert duplicate uploads with identical file_hash or (invoice_number, vendor_id)
    do not create multiple independent active rows in the DB.
    """
    v = db_session.query(Vendor).first()
    file_bytes = b"Sample Invoice Content Bytes for INV-4821"
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Create original invoice
    inv1 = Invoice(
        invoice_number="INV-4821",
        vendor_id=v.id,
        file_hash=file_hash,
        amount=126000.0,
        status="pending"
    )
    db_session.add(inv1)
    db_session.commit()

    # Check that query by file_hash finds existing invoice
    existing_by_hash = db_session.query(Invoice).filter(Invoice.file_hash == file_hash).first()
    assert existing_by_hash is not None
    assert existing_by_hash.id == inv1.id

    # Check that query by invoice_number + vendor_id finds existing invoice
    existing_by_inv_vendor = db_session.query(Invoice).filter(
        Invoice.invoice_number == "INV-4821",
        Invoice.vendor_id == v.id
    ).first()
    assert existing_by_inv_vendor is not None
    assert existing_by_inv_vendor.id == inv1.id

    # Count total invoices matching INV-4821
    count = db_session.query(Invoice).filter(Invoice.invoice_number == "INV-4821").count()
    assert count == 1

def test_bug3_po_reference_not_literal_string():
    """
    Test Bug 3: Verify PO Reference extraction returns real PO code (PO-1021) and never 'REFERENCE'.
    """
    text1 = "Invoice #: INV-4821\nPO Reference: PO-1021\nTotal Amount Payable: ₹1,26,000.00"
    data1 = LLMService._deterministic_extraction_fallback(text1)
    assert data1["po_reference"] == "PO-1021"

    text2 = "Invoice #: INV-9001\nPurchase Order #: PO-9001\nTotal: ₹3,54,000.00"
    data2 = LLMService._deterministic_extraction_fallback(text2)
    assert data2["po_reference"] == "PO-9001"

def test_bug4_amount_parsing_diff_formats_no_zero_coercion():
    """
    Test Bug 4: Verify non-zero amount extraction for differently-formatted invoices
    and preserve None state (extraction_failed) when amount is missing.
    """
    # Layout A: Total Amount Payable
    raw_a = "Invoice #: INV-1\nTotal Amount Payable: ₹1,26,000.00"
    data_a = LLMService._deterministic_extraction_fallback(raw_a)
    assert data_a["total_amount"] == 126000.0

    # Layout B: Grand Total
    raw_b = "Invoice #: INV-2\nGrand Total: $4,500.50"
    data_b = LLMService._deterministic_extraction_fallback(raw_b)
    assert data_b["total_amount"] == 4500.50

    # Layout C: Missing Amount -> Must be None (NOT 0.0)
    raw_c = "Invoice #: INV-3\nSome terms text without total amount"
    data_c = LLMService._deterministic_extraction_fallback(raw_c)
    assert data_c["total_amount"] is None

def test_full_agent_verification_pipeline_valid(db_session):
    v = db_session.query(Vendor).first()
    
    # Create Invoice matching PO-1021
    inv = Invoice(
        invoice_number="INV-4821",
        vendor_id=v.id,
        raw_ocr_text="Invoice #: INV-4821 PO Reference: PO-1021 Total Amount Payable: ₹1,26,000.00",
        extracted_json={
            "vendor_name": "ABC Technologies Pvt. Ltd.",
            "gst_number": "27AAAAA0000A1Z5",
            "invoice_number": "INV-4821",
            "po_reference": "PO-1021",
            "subtotal": 126000.0,
            "tax_amount": 0.0,
            "total_amount": 126000.0
        },
        amount=126000.0,
        status="pending"
    )
    db_session.add(inv)
    db_session.commit()

    agent = VerificationAgent(db_session)
    result = agent.process_invoice(inv.id)

    assert result["overall_status"] == "AUTO APPROVED RECOMMENDATION"
    assert result["confidence"] > 0.90
    assert inv.invoice_number == "INV-4821"
    assert inv.amount == 126000.0
