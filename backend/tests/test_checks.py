import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models import Vendor, PurchaseOrder, Invoice, InvoiceStatus
from app.services.tool_registry import VerificationTools

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed test vendor & PO
    v = Vendor(name="Test Vendor Pvt Ltd", gst_number="27AAAAA0000A1Z5")
    session.add(v)
    session.commit()

    po = PurchaseOrder(
        po_number="PO-TEST-100",
        vendor_id=v.id,
        product_name="Test Widget",
        quantity=10,
        unit_price=100.0,
        total_amount=1000.0
    )
    session.add(po)
    session.commit()

    yield session
    session.close()

def test_tool_duplicate_check_pass(db):
    v = db.query(Vendor).first()
    res = VerificationTools.tool_duplicate_check("INV-UNIQUE-1", v.id, current_invoice_id=99, db=db)
    assert res["result"] == "pass"
    assert "valid" in res["summary"]

def test_tool_duplicate_check_fail(db):
    v = db.query(Vendor).first()
    # Add existing invoice
    inv = Invoice(invoice_number="INV-DUP-1", vendor_id=v.id, amount=500.0, status=InvoiceStatus.APPROVED_BY_HUMAN.value)
    db.add(inv)
    db.commit()

    res = VerificationTools.tool_duplicate_check("INV-DUP-1", v.id, current_invoice_id=999, db=db)
    assert res["result"] == "fail"
    assert res["details"]["is_duplicate"] is True

def test_tool_po_match_pass(db):
    v = db.query(Vendor).first()
    res = VerificationTools.tool_po_match("PO-TEST-100", v.id, 1000.0, [], db)
    assert res["result"] == "pass"
    assert res["details"]["po_amount"] == 1000.0

def test_tool_po_match_exceeds_amount(db):
    v = db.query(Vendor).first()
    # Invoice is 1500 vs PO 1000
    res = VerificationTools.tool_po_match("PO-TEST-100", v.id, 1500.0, [], db)
    assert res["result"] == "fail"
    assert "exceeds PO" in res["summary"]

def test_tool_gst_tax_check(db):
    v = db.query(Vendor).first()
    res = VerificationTools.tool_gst_tax_check(
        extracted_gst="27AAAAA0000A1Z5",
        vendor_id=v.id,
        subtotal=1000.0,
        tax_amount=180.0,
        total_amount=1180.0,
        db=db
    )
    assert res["result"] == "pass"
