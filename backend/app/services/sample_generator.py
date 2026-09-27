import os
import fitz  # PyMuPDF

def generate_sample_invoices(output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    samples = [
        {
            "filename": "sample_invoice_INV-4821.pdf",
            "content": """===================================================
ABC Technologies Pvt. Ltd.
Plot 14, Hitech City Road, Madhapur, Hyderabad - 500081
GSTIN: 27AAAAA0000A1Z5
Contact: billing@abctech.com | Phone: +91 40 4000 1234

INVOICE DETAILS
---------------------------------------------------
Invoice #: INV-4821
Invoice Date: 2026-09-15
PO Reference: PO-1021

Bill To: Enterprise Finance Corp
Shipping Address: Building 4, Cyber City, Gurgaon

Line Items:
Item Description             Qty    Unit Price    Total
---------------------------------------------------
Enterprise Software License   1      ₹1,26,000     ₹1,26,000

Subtotal: ₹1,26,000
GST (0%): ₹0
Total Amount Payable: ₹1,26,000.00
==================================================="""
        },
        {
            "filename": "invoice_valid_abc_tech.pdf",
            "content": """===================================================
ABC Technologies Pvt. Ltd.
Plot 14, Hitech City Road, Hyderabad - 500081
GSTIN: 27AAAAA0000A1Z5

INVOICE DETAILS
---------------------------------------------------
Invoice #: INV-9001
Invoice Date: 2026-09-16
PO Reference: PO-9001

Bill To: Enterprise Finance Corp

Item Description             Qty    Unit Price    Total
---------------------------------------------------
Dell UltraSharp Monitor 27"   10     ₹25,000      ₹2,50,000
Ergonomic Mesh Chair          5      ₹10,000      ₹50,000

Subtotal: ₹3,000,000
GST (18%): ₹54,000
Total Amount Payable: ₹3,54,000.00
==================================================="""
        },
        {
            "filename": "invoice_po_mismatch_xyz.pdf",
            "content": """===================================================
XYZ Logistics Solutions
Plot 88, Freight Logistics Park, New Delhi - 110001
GSTIN: 07BBBBB1111B2Z8

INVOICE DETAILS
---------------------------------------------------
Invoice #: INV-8920
Invoice Date: 2026-09-20
PO Reference: PO-9002

Bill To: Enterprise Finance Corp

Item Description             Qty    Unit Price    Total
---------------------------------------------------
Express Freight Service       1      ₹1,26,000     ₹1,26,000

Subtotal: ₹1,26,000
GST (18%): ₹22,680
Total Amount Payable: ₹1,48,680.00
==================================================="""
        },
        {
            "filename": "invoice_duplicate_global.pdf",
            "content": """===================================================
Global Cloud Services
Building B, Tech Park, Bengaluru - 560100
GSTIN: 29CCCCC2222C3Z1

INVOICE DETAILS
---------------------------------------------------
Invoice #: INV-4821
Invoice Date: 2026-09-22
PO Reference: PO-9003

Bill To: Enterprise Finance Corp

Item Description             Qty    Unit Price    Total
---------------------------------------------------
Cloud Storage Subscription    1      ₹45,000       ₹45,000

Subtotal: ₹45,000
GST (18%): ₹8,100
Total Amount Payable: ₹53,100.00
==================================================="""
        },
        {
            "filename": "invoice_high_amount_acme.pdf",
            "content": """===================================================
Acme Office Supplies
Plot 42, Industrial Area, Chennai - 600001
GSTIN: 33DDDDD3333D4Z4

INVOICE DETAILS
---------------------------------------------------
Invoice #: INV-9901
Invoice Date: 2026-09-25
PO Reference: PO-9004

Bill To: Enterprise Finance Corp

Item Description             Qty    Unit Price    Total
---------------------------------------------------
Enterprise Server Rack        2      ₹4,50,000     ₹9,00,000

Subtotal: ₹9,00,000
GST (18%): ₹1,62,000
Total Amount Payable: ₹10,62,000.00
==================================================="""
        }
    ]

    for sample in samples:
        filepath = os.path.join(output_dir, sample["filename"])
        doc = fitz.open()
        page = doc.new_page()
        point = fitz.Point(50, 50)
        page.insert_text(point, sample["content"], fontsize=11)
        doc.save(filepath)
        doc.close()

    print(f"Generated {len(samples)} sample PDF invoices in {output_dir}")

if __name__ == "__main__":
    generate_sample_invoices("samples")
