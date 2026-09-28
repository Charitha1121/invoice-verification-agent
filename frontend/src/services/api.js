const API_BASE = "http://localhost:8000/api/v1";

export async function fetchInvoices(statusFilter = null) {
  const url = statusFilter 
    ? `${API_BASE}/invoices?status=${encodeURIComponent(statusFilter)}` 
    : `${API_BASE}/invoices`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch invoices");
  return res.json();
}

export async function fetchInvoiceDetails(id) {
  const res = await fetch(`${API_BASE}/invoices/${id}`);
  if (!res.ok) throw new Error("Failed to fetch invoice details");
  return res.json();
}

export async function uploadInvoiceFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/invoices/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || "Failed to upload invoice");
  }
  return res.json();
}

export async function reviewInvoice(id, action, notes = "") {
  const res = await fetch(`${API_BASE}/invoices/${id}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action, notes }),
  });
  if (!res.ok) throw new Error("Failed to submit review");
  return res.json();
}

export async function rerunAgent(id) {
  const res = await fetch(`${API_BASE}/invoices/${id}/rerun`, { method: "POST" });
  if (!res.ok) throw new Error("Failed to rerun agent verification");
  return res.json();
}

export async function listSamplePresets() {
  const res = await fetch(`${API_BASE}/invoices/samples/list`);
  if (!res.ok) throw new Error("Failed to list sample presets");
  return res.json();
}

export async function processSamplePreset(sampleName) {
  const res = await fetch(`${API_BASE}/invoices/process-sample/${encodeURIComponent(sampleName)}`, {
    method: "POST"
  });
  if (!res.ok) throw new Error("Failed to process sample preset");
  return res.json();
}

export async function fetchVendors() {
  const res = await fetch(`${API_BASE}/vendors`);
  if (!res.ok) throw new Error("Failed to fetch vendors");
  return res.json();
}

export async function fetchVendorProfile(vendorId) {
  const res = await fetch(`${API_BASE}/vendors/${vendorId}/profile`);
  if (!res.ok) throw new Error("Failed to fetch vendor profile");
  return res.json();
}

export async function fetchPurchaseOrders() {
  const res = await fetch(`${API_BASE}/pos`);
  if (!res.ok) throw new Error("Failed to fetch POs");
  return res.json();
}

export async function queryInvoicesNL(queryText) {
  const res = await fetch(`${API_BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: queryText })
  });
  if (!res.ok) throw new Error("Natural language query failed");
  return res.json();
}
