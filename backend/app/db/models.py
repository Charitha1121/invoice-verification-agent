from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.database import Base

class InvoiceStatus(str, enum.Enum):
    PENDING = "pending"
    AUTO_APPROVED = "auto_approved"
    FLAGGED = "flagged"
    REJECTED = "rejected"
    APPROVED_BY_HUMAN = "approved_by_human"
    EXTRACTION_FAILED = "extraction_failed"

class CheckResult(str, enum.Enum):
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    FINANCE_USER = "finance_user"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.FINANCE_USER.value)
    created_at = Column(DateTime, default=datetime.utcnow)

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    gst_number = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    pos = relationship("PurchaseOrder", back_populates="vendor")
    invoices = relationship("Invoice", back_populates="vendor")

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(100), unique=True, nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    product_name = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    line_items = Column(JSON, nullable=True) # Detailed list of PO items
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="pos")
    invoices = relationship("Invoice", back_populates="po")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), nullable=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id"), nullable=True)
    duplicate_of_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    
    file_hash = Column(String(64), nullable=True, index=True)
    raw_ocr_text = Column(Text, nullable=True)
    extracted_json = Column(JSON, nullable=True) # Extracted vendor, invoice_no, amount, line_items, date, GST, PO_ref
    amount = Column(Float, nullable=True, default=None)
    invoice_date = Column(String(50), nullable=True)
    file_name = Column(String(255), nullable=True)
    
    status = Column(String(50), default=InvoiceStatus.PENDING.value, index=True)
    risk_score = Column(Float, default=0.0) # 0.0 to 1.0 confidence/risk
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="invoices")
    po = relationship("PurchaseOrder", back_populates="invoices")
    checks = relationship("InvoiceCheck", back_populates="invoice", cascade="all, delete-orphan")
    risk_report = relationship("RiskReport", back_populates="invoice", uselist=False, cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="invoice", cascade="all, delete-orphan")

class InvoiceCheck(Base):
    __tablename__ = "invoice_checks"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    check_type = Column(String(100), nullable=False) # e.g., duplicate_check, po_match, vendor_history, gst_check, amount_threshold
    result = Column(String(20), nullable=False) # pass, fail, warning
    details_json = Column(JSON, nullable=True) # Explanation, quantitative diffs, metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="checks")

class RiskReport(Base):
    __tablename__ = "risk_reports"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, unique=True)
    overall_status = Column(String(100), nullable=False) # e.g. "HUMAN REVIEW REQUIRED", "AUTO APPROVED RECOMMENDATION", "HIGH RISK"
    summary_text = Column(Text, nullable=False)
    confidence = Column(Float, default=1.0)
    tool_steps_json = Column(JSON, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="risk_report")

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    actor = Column(String(100), nullable=False) # "Agent Orchestrator", "User (finance_user)", "User (admin)"
    action = Column(String(255), nullable=False) # e.g., "Extracted OCR & structured data", "Executed deterministic checks", "Human Approved"
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", back_populates="audit_logs")
