from sqlalchemy.orm import Session
from app.db.database import engine, Base, SessionLocal
from app.db.models import User, Vendor, PurchaseOrder, UserRole, Invoice, InvoiceStatus, AuditLog
from app.api.auth import get_password_hash
from app.services.sample_generator import generate_sample_invoices
from app.services.verification_agent import VerificationAgent
from app.services.ocr_service import OCRService
from app.services.llm_service import LLMService
import os
import hashlib

def seed_database():
    print("Initializing Database tables...")
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # 1. Create Default Users if not exist
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@finance-corp.com",
                hashed_password=get_password_hash("admin123"),
                role=UserRole.ADMIN.value
            )
            db.add(admin)

        finance_user = db.query(User).filter(User.username == "finance_user").first()
        if not finance_user:
            finance_user = User(
                username="finance_user",
                email="finance@finance-corp.com",
                hashed_password=get_password_hash("finance123"),
                role=UserRole.FINANCE_USER.value
            )
            db.add(finance_user)

        db.commit()
        print("[OK] Users seeded: admin (admin123), finance_user (finance123)")

        # 2. Create Vendors if not exist
        v_abc = db.query(Vendor).filter(Vendor.name == "ABC Technologies Pvt. Ltd.").first()
        if not v_abc:
            v_abc = Vendor(name="ABC Technologies Pvt. Ltd.", gst_number="27AAAAA0000A1Z5")
            db.add(v_abc)

        v_xyz = db.query(Vendor).filter(Vendor.name == "XYZ Logistics Solutions").first()
        if not v_xyz:
            v_xyz = Vendor(name="XYZ Logistics Solutions", gst_number="07BBBBB1111B2Z8")
            db.add(v_xyz)

        v_global = db.query(Vendor).filter(Vendor.name == "Global Cloud Services").first()
        if not v_global:
            v_global = Vendor(name="Global Cloud Services", gst_number="29CCCCC2222C3Z1")
            db.add(v_global)

        v_acme = db.query(Vendor).filter(Vendor.name == "Acme Office Supplies").first()
        if not v_acme:
            v_acme = Vendor(name="Acme Office Supplies", gst_number="33DDDDD3333D4Z4")
            db.add(v_acme)

        db.commit()
        db.refresh(v_abc)
        db.refresh(v_xyz)
        db.refresh(v_global)
        db.refresh(v_acme)
        print("[OK] Vendors seeded")

        # 3. Create Purchase Orders if not exist
        po_1021 = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-1021").first()
        if not po_1021:
            po_1021 = PurchaseOrder(
                po_number="PO-1021",
                vendor_id=v_abc.id,
                product_name="Enterprise Software License",
                quantity=1,
                unit_price=126000.0,
                total_amount=126000.0,
                line_items=[
                    {"description": "Enterprise Software License", "quantity": 1, "unit_price": 126000.0, "total": 126000.0}
                ]
            )
            db.add(po_1021)

        po1 = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-9001").first()
        if not po1:
            po1 = PurchaseOrder(
                po_number="PO-9001",
                vendor_id=v_abc.id,
                product_name="Dell Monitors & Mesh Chairs",
                quantity=15,
                unit_price=23600.0,
                total_amount=354000.0,
                line_items=[
                    {"description": 'Dell UltraSharp Monitor 27"', "quantity": 10, "unit_price": 25000.0, "total": 250000.0},
                    {"description": "Ergonomic Mesh Chair", "quantity": 5, "unit_price": 10000.0, "total": 50000.0}
                ]
            )
            db.add(po1)

        po2 = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-9002").first()
        if not po2:
            po2 = PurchaseOrder(
                po_number="PO-9002",
                vendor_id=v_xyz.id,
                product_name="Express Freight Service",
                quantity=1,
                unit_price=94000.0,
                total_amount=94000.0,
                line_items=[
                    {"description": "Express Freight Service", "quantity": 1, "unit_price": 94000.0, "total": 94000.0}
                ]
            )
            db.add(po2)

        po3 = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-9003").first()
        if not po3:
            po3 = PurchaseOrder(
                po_number="PO-9003",
                vendor_id=v_global.id,
                product_name="Cloud Storage Subscription",
                quantity=1,
                unit_price=45000.0,
                total_amount=53100.0,
                line_items=[
                    {"description": "Cloud Storage Subscription", "quantity": 1, "unit_price": 45000.0, "total": 53100.0}
                ]
            )
            db.add(po3)

        po4 = db.query(PurchaseOrder).filter(PurchaseOrder.po_number == "PO-9004").first()
        if not po4:
            po4 = PurchaseOrder(
                po_number="PO-9004",
                vendor_id=v_acme.id,
                product_name="Enterprise Server Rack",
                quantity=2,
                unit_price=450000.0,
                total_amount=1062000.0,
                line_items=[
                    {"description": "Enterprise Server Rack", "quantity": 2, "unit_price": 450000.0, "total": 1062000.0}
                ]
            )
            db.add(po4)

        db.commit()
        print("[OK] Purchase Orders seeded")

        # 4. Create Historical Approved Invoices for Vendor Average calculations
        past_inv1 = db.query(Invoice).filter(Invoice.invoice_number == "INV-HIST-101").first()
        if not past_inv1:
            past_inv1 = Invoice(
                invoice_number="INV-HIST-101",
                vendor_id=v_acme.id,
                amount=48000.0,
                invoice_date="2026-08-10",
                status=InvoiceStatus.APPROVED_BY_HUMAN.value,
                extracted_json={"vendor_name": "Acme Office Supplies", "total_amount": 48000.0}
            )
            db.add(past_inv1)

        past_inv2 = db.query(Invoice).filter(Invoice.invoice_number == "INV-HIST-102").first()
        if not past_inv2:
            past_inv2 = Invoice(
                invoice_number="INV-HIST-102",
                vendor_id=v_acme.id,
                amount=52000.0,
                invoice_date="2026-08-25",
                status=InvoiceStatus.APPROVED_BY_HUMAN.value,
                extracted_json={"vendor_name": "Acme Office Supplies", "total_amount": 52000.0}
            )
            db.add(past_inv2)

        db.commit()
        print("[OK] Historical invoices seeded for rolling average baseline")

        # 5. Generate sample PDF files & ingest them into DB
        samples_dir = os.path.join("..", "samples")
        generate_sample_invoices(samples_dir)

        sample_files = [
            "sample_invoice_INV-4821.pdf",
            "invoice_valid_abc_tech.pdf",
            "invoice_po_mismatch_xyz.pdf",
            "invoice_duplicate_global.pdf",
            "invoice_high_amount_acme.pdf"
        ]

        for sfile in sample_files:
            filepath = os.path.join(samples_dir, sfile)
            if os.path.exists(filepath):
                with open(filepath, "rb") as f:
                    file_bytes = f.read()

                file_hash = hashlib.sha256(file_bytes).hexdigest()
                existing_inv = db.query(Invoice).filter(Invoice.file_hash == file_hash).first()

                if not existing_inv:
                    ocr_res = OCRService.extract_text_from_file(file_bytes, sfile)
                    ext_json = LLMService.extract_structured_invoice_data(ocr_res["raw_text"])
                    inv_no = ext_json.get("invoice_number")
                    v_name = ext_json.get("vendor_name")
                    tot_amt = ext_json.get("total_amount")

                    target_v = None
                    if v_name:
                        target_v = db.query(Vendor).filter(Vendor.name.ilike(f"%{v_name}%")).first()

                    db_inv = Invoice(
                        invoice_number=inv_no,
                        vendor_id=target_v.id if target_v else None,
                        file_hash=file_hash,
                        raw_ocr_text=ocr_res["raw_text"],
                        extracted_json=ext_json,
                        amount=tot_amt,
                        invoice_date=ext_json.get("invoice_date"),
                        file_name=sfile,
                        status=InvoiceStatus.PENDING.value if (inv_no and tot_amt) else InvoiceStatus.EXTRACTION_FAILED.value
                    )
                    db.add(db_inv)
                    db.commit()
                    db.refresh(db_inv)

                    if inv_no and tot_amt:
                        agent = VerificationAgent(db)
                        agent.process_invoice(db_inv.id)

        print("[OK] Preset sample invoices ingested and processed through Verification Agent")
        print("Seed completed successfully!")

    except Exception as e:
        print(f"Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
