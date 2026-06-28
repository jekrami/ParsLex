const API_BASE = import.meta.env.VITE_API_BASE ?? "/api/v1";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  created_at: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
}

export interface DocumentVersion {
  id: string;
  file_name: string;
  file_size: number;
  version_number: number;
}

export interface Document {
  id: string;
  title: string;
  document_type: string;
  language: string;
  status: string;
  created_at: string;
  current_version?: DocumentVersion;
}

export interface AuditEvent {
  id: string;
  action: string;
  resource_type: string;
  user_email?: string;
  created_at: string;
  metadata: Record<string, unknown>;
}

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}` };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || err.detail || "Request failed");
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return handleResponse<{ access_token: string; user: User }>(res);
}

export async function getMe(token: string) {
  const res = await fetch(`${API_BASE}/auth/me`, { headers: authHeaders(token) });
  return handleResponse<User>(res);
}

export async function listOrganizations(token: string) {
  const res = await fetch(`${API_BASE}/organizations`, { headers: authHeaders(token) });
  return handleResponse<{ items: Organization[] }>(res);
}

export async function listDocuments(token: string, orgId: string) {
  const res = await fetch(`${API_BASE}/organizations/${orgId}/documents`, {
    headers: authHeaders(token),
  });
  return handleResponse<{ items: Document[]; total: number }>(res);
}

export async function uploadDocument(
  token: string,
  orgId: string,
  file: File,
  title: string,
  documentType: string
) {
  const form = new FormData();
  form.append("file", file);
  form.append("title", title);
  form.append("document_type", documentType);
  const res = await fetch(`${API_BASE}/organizations/${orgId}/documents`, {
    method: "POST",
    headers: authHeaders(token),
    body: form,
  });
  return handleResponse<Document>(res);
}

export async function listAuditEvents(token: string, orgId: string) {
  const res = await fetch(`${API_BASE}/organizations/${orgId}/audit/events`, {
    headers: authHeaders(token),
  });
  return handleResponse<{ items: AuditEvent[]; total: number }>(res);
}

export async function deleteDocument(token: string, orgId: string, docId: string) {
  const res = await fetch(`${API_BASE}/organizations/${orgId}/documents/${docId}`, {
    method: "DELETE",
    headers: authHeaders(token),
  });
  return handleResponse<void>(res);
}
