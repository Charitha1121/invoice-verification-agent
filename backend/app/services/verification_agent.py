from sqlalchemy.orm import Session
from app.db.models import (
    Invoice, Vendor, InvoiceCheck, RiskReport, AuditLog,
    InvoiceStatus, CheckResult
)
from app.services.tool_registry import VerificationTools
from app.services.llm_service import LLMService

class VerificationAgent:
    def __init__(self, db: Session):
        self.db = db

    def process_invoice(self, invoice_id: int) -> dict:
        """
        Executes the explicit tool-calling verification loop on an ingested invoice.
        """
        invoice = self.db.query(Invoice).get(invoice_id)
        if not invoice:
            raise ValueError(f"Invoice ID {invoice_id} not found")

        extracted_data = invoice.extracted_json or {}
        vendor_name = extracted_data.get("vendor_name", "Unknown Vendor")
        gst_number = extracted_data.get("gst_number")
        invoice_number = invoice.invoice_number or extracted_data.get("invoice_number", "UNKNOWN-INV")
        po_reference = extracted_data.get("po_reference")
        total_amount = invoice.amount or extracted_data.get("total_amount", 0.0)
        subtotal = extracted_data.get("subtotal", 0.0)
        tax_amount = extracted_data.get("tax_amount", 0.0)
        line_items = extracted_data.get("line_items", [])

        # 1. Vendor Lookup or Registration
        vendor = None
        if vendor_name and vendor_name != "Unknown Vendor":
            vendor = self.db.query(Vendor).filter(Vendor.name.ilike(f"%{vendor_name}%")).first()
            if not vendor and gst_number:
                vendor = self.db.query(Vendor).filter(Vendor.gst_number == gst_number).first()
            
            if not vendor:
                vendor = Vendor(name=vendor_name, gst_number=gst_number)
                self.db.add(vendor)
                self.db.commit()
                self.db.refresh(vendor)

        if vendor:
            invoice.vendor_id = vendor.id

        # 2. Dynamic Tool Calling Execution Plan
        tool_execution_plan = [
            "duplicate_check",
            "po_match",
            "vendor_history",
            "gst_tax_check"
        ]

        executed_checks = []
        tool_steps_log = []

        # Execute Tool 1: Duplicate Check
        dup_result = VerificationTools.tool_duplicate_check(
            invoice_number=invoice_number,
            vendor_id=vendor.id if vendor else None,
            current_invoice_id=invoice.id,
            db=self.db
        )
        executed_checks.append(dup_result)
        tool_steps_log.append({
            "tool": "duplicate_check",
            "inputs": {"invoice_number": invoice_number, "vendor_id": vendor.id if vendor else None},
            "output": dup_result
        })

        # Execute Tool 2: PO Match
        po_result = VerificationTools.tool_po_match(
            po_reference=po_reference,
            vendor_id=vendor.id if vendor else None,
            invoice_amount=total_amount,
            extracted_items=line_items,
            db=self.db
        )
        executed_checks.append(po_result)
        tool_steps_log.append({
            "tool": "po_match",
            "inputs": {"po_reference": po_reference, "invoice_amount": total_amount},
            "output": po_result
        })

        # Attach PO relation if matched
        if po_result.get("details", {}).get("po_id"):
            invoice.po_id = po_result["details"]["po_id"]

        # Execute Tool 3: Vendor History Check
        history_result = VerificationTools.tool_vendor_history_check(
            vendor_id=vendor.id if vendor else None,
            current_amount=total_amount,
            db=self.db
        )
        executed_checks.append(history_result)
        tool_steps_log.append({
            "tool": "vendor_history",
            "inputs": {"vendor_id": vendor.id if vendor else None, "current_amount": total_amount},
            "output": history_result
        })

        # Execute Tool 4: GST / Tax Check
        gst_result = VerificationTools.tool_gst_tax_check(
            extracted_gst=gst_number,
            vendor_id=vendor.id if vendor else None,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            db=self.db
        )
        executed_checks.append(gst_result)
        tool_steps_log.append({
            "tool": "gst_tax_check",
            "inputs": {"extracted_gst": gst_number, "subtotal": subtotal, "tax_amount": tax_amount, "total_amount": total_amount},
            "output": gst_result
        })

        # 3. Persist individual InvoiceCheck records
        # Clear old checks if re-running
        self.db.query(InvoiceCheck).filter(InvoiceCheck.invoice_id == invoice.id).delete()
        
        for c in executed_checks:
            db_check = InvoiceCheck(
                invoice_id=invoice.id,
                check_type=c["check_type"],
                result=c["result"],
                details_json=c
            )
            self.db.add(db_check)

        # 4. Calculate overall Risk Confidence Score & Verdict
        has_failure = any(c["result"] == CheckResult.FAIL.value for c in executed_checks)
        has_warning = any(c["result"] == CheckResult.WARNING.value for c in executed_checks)

        if has_failure:
            confidence = 0.65 if has_warning else 0.75
            status = InvoiceStatus.FLAGGED.value
        elif has_warning:
            confidence = 0.85
            status = InvoiceStatus.FLAGGED.value
        else:
            confidence = 0.98
            status = InvoiceStatus.AUTO_APPROVED.value # Note: Still requires human final sign-off or auto status recommendation

        verdict = LLMService.synthesize_agent_verdict(
            invoice_no=invoice_number,
            vendor_name=vendor_name,
            checks=executed_checks,
            confidence=confidence
        )

        invoice.status = status
        invoice.risk_score = 1.0 - confidence # High risk = low confidence

        # 5. Persist Risk Report
        existing_report = self.db.query(RiskReport).filter(RiskReport.invoice_id == invoice.id).first()
        if existing_report:
            existing_report.overall_status = verdict["overall_status"]
            existing_report.summary_text = verdict["summary_text"]
            existing_report.confidence = confidence
            existing_report.tool_steps_json = tool_steps_log
        else:
            report = RiskReport(
                invoice_id=invoice.id,
                overall_status=verdict["overall_status"],
                summary_text=verdict["summary_text"],
                confidence=confidence,
                tool_steps_json=tool_steps_log
            )
            self.db.add(report)

        # 6. Audit Log
        audit = AuditLog(
            invoice_id=invoice.id,
            actor="Agent Orchestrator",
            action=f"Verification tool pipeline completed. Result: {verdict['overall_status']}",
            notes=f"Executed {len(executed_checks)} checks ({sum(1 for c in executed_checks if c['result'] == 'pass')} Passed, {sum(1 for c in executed_checks if c['result'] == 'fail')} Failed, {sum(1 for c in executed_checks if c['result'] == 'warning')} Warnings)"
        )
        self.db.add(audit)

        self.db.commit()
        self.db.refresh(invoice)

        return {
            "invoice_id": invoice.id,
            "status": invoice.status,
            "risk_score": invoice.risk_score,
            "overall_status": verdict["overall_status"],
            "summary_text": verdict["summary_text"],
            "confidence": confidence,
            "checks": executed_checks
        }
