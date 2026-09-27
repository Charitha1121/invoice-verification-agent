# 🧾 AI-Powered Accounts Payable Verification Agent

> **One-Line Pitch:** An AI-powered accounts-payable verification system that uses OCR and LLMs to understand invoices, then applies deterministic validation and vendor-history analysis to flag exceptions for human review before payment.

---

## 1. System Architecture

```
Upload Invoice (PDF / Image Scan)
            ↓
       [OCR Layer] → Raw Text Extraction (PyMuPDF / Tesseract)
            ↓
     [LLM Extraction] → Structured JSON (Vendor, Invoice No, Amount, Dates, Line Items, PO Ref)
            ↓
  [PostgreSQL / Database] → Persist Raw Invoices & Line Items
            ↓
  [Verification Agent Orchestrator] ◄── Tool Loop
       ├── 1. Tool: Duplicate Check (Invoice No + Vendor Uniqueness)
       ├── 2. Tool: PO Match (Query POs table, 3-way line item match, qty/unit price)
       ├── 3. Tool: Vendor History Check (Rolling average amount, past mismatch rates)
       └── 4. Tool: GST / Tax Field Verification (Format, Tax math consistency)
            ↓
    [Structured Risk Report] → Status Verdict (AUTO APPROVED, HUMAN REVIEW REQUIRED)
            ↓
   [React Executive Dashboard] → Flagged Queue, 3-Way Inspector, Audit Log & Human Actions
```

---

## 2. Tech Stack & Justifications

- **Backend:** Python 3.12, FastAPI (Async, Pydantic V2 schemas, OpenAPI docs)
- **Database:** PostgreSQL (SQLAlchemy 2.0 ORM with SQLite local fallback out-of-the-box)
- **OCR Engine:** Tesseract OCR + PyMuPDF / pdfplumber parser.
  - *Justification:* Tesseract + PyMuPDF provides a zero-latency, privacy-compliant, self-hosted open-source solution that avoids per-page API fees incurred by cloud OCR APIs (e.g. AWS Textract / Google Document AI). For digital PDFs, PyMuPDF extracts vectors and text instantly with 100% precision.
- **LLM Layer:** Flexible Agent service supporting Google Gemini API / OpenAI API, plus a smart deterministic rule-based LLM fallback when API keys are omitted.
- **Frontend:** React (Vite), Tailwind CSS v4, Lucide Icons, Glassmorphic UI.
- **Auth:** JWT-based role separation (`Finance Specialist` vs `Lead Auditor`).

---

## 3. Agent Tool-Calling Architecture (Interview Talking Points)

### Why an explicit Tool-Calling loop instead of a single giant prompt?
Traditional LLM wrappers suffer from two fatal vulnerabilities when applied to financial workflows:
1. **Hallucination Risk:** Single-prompt LLMs will invent PO numbers, hallucinate database records, or miscalculate line-item tax math.
2. **Lack of Auditability:** Financial compliance (SOX, SOC2) requires deterministic proof for *why* an invoice was flagged or approved.

**Our Agent Orchestration Pattern:**
- **Deterministic Guardrails:** The LLM does not write raw SQL or execute arithmetic directly. Instead, it inspects the extracted invoice metadata and triggers parameter-validated Python functions (`tool_duplicate_check`, `tool_po_match`, `tool_vendor_history_check`, `tool_gst_tax_check`).
- **Explicit Fact Gathers:** The orchestrator executes tools step-by-step, logging inputs, returned dictionary facts, and exact variance percentages (`+34.0% deviation`).
- **Explainability First:** Synthesizes a human-readable risk summary matching exact financial compliance standards:
  ```
  Invoice: INV-4821
  Vendor: ABC Technologies Pvt Ltd

  ✓ Vendor verified
  ✓ Invoice number valid (no duplicate)
  ✗ Amount exceeds PO by ₹32,000
  ⚠ Vendor's average invoice: ₹48,000
  ⚠ Current invoice: ₹1,26,000

  Status: HUMAN REVIEW REQUIRED
  Confidence: 0.82
  ```

---

## 4. Quickstart & Running Locally

### Option A: Local Quickstart (No Docker required)

1. **Clone & Install Backend:**
   ```bash
   cd backend
   py -3 -m pip install -r requirements.txt
   ```

2. **Seed Database & Run Backend Server:**
   ```bash
   py -3 -m app.seed
   py -3 -m uvicorn app.main:app --reload --port 8000
   ```
   *The database is automatically seeded with sample vendors, purchase orders, historical invoice baselines, and 4 test invoices!*

3. **Install & Run Frontend:**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
   Open `http://localhost:5173` in your browser!

---

### Option B: Launch with Docker Compose (PostgreSQL + Tesseract + Nginx)

```bash
docker-compose up --build
```
- Frontend: `http://localhost`
- Backend API & Swagger Docs: `http://localhost:8000/docs`
- PostgreSQL: `localhost:5432`

---

## 5. Test Suite & Verification

Run unit & integration tests on deterministic tools and full agent pipelines:
```bash
py -3 -m pytest backend/tests
```
- `test_checks.py`: Unit tests for duplicate detection, PO amount variances, and GST math.
- `test_pipeline.py`: End-to-end integration test verifying agent verdicts for clean PO matches vs PO amount mismatches.

---

## 6. Pre-seeded Demo Scenarios

When you open the web dashboard or click **"+ Ingest New Invoice"**, you can test 4 pre-configured real-world financial edge cases with 1 click:

1. **Preset 1: `invoice_valid_abc_tech.pdf` (Clean Match)**
   - PO: `PO-9001` | Amount: `₹3,54,000.00`
   - Verdict: `AUTO APPROVED RECOMMENDATION` (100% PO & GST Match)
2. **Preset 2: `invoice_po_mismatch_xyz.pdf` (PO Price Variance)**
   - PO: `PO-9002` (Agreed: ₹94,000) vs Invoice Claim: `₹1,26,000.00`
   - Verdict: `HUMAN REVIEW REQUIRED` (`✗ Amount exceeds PO by ₹32,000`)
3. **Preset 3: `invoice_duplicate_global.pdf` (Duplicate Re-upload)**
   - Re-submits invoice number `INV-4821` already present in database
   - Verdict: `HUMAN REVIEW REQUIRED` (`✗ Duplicate invoice detected`)
4. **Preset 4: `invoice_high_amount_acme.pdf` (Unusual Deviation)**
   - Claim: `₹10,62,000.00` vs Historical Vendor Average: `₹50,000.00`
   - Verdict: `HUMAN REVIEW REQUIRED` (`⚠ High deviation >2.5x historical average`)

---

## 7. Production Deployment Guide

- **Render / Railway Deployment:**
  - Build Backend Docker container pointing to a managed PostgreSQL instance (e.g. Render Postgres / Supabase).
  - Environment variables: `DATABASE_URL`, `SECRET_KEY`, `GEMINI_API_KEY`.
- **AWS Deployment (Production Enterprise):**
  - **Database:** AWS RDS PostgreSQL
  - **Backend Services:** AWS ECS Fargate container running FastAPI backend with S3 bucket for invoice PDF archival.
  - **Frontend:** AWS CloudFront + S3 static hosting.
