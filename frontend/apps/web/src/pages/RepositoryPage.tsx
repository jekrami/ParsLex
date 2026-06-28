import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import {
  deleteDocument,
  listDocuments,
  listOrganizations,
  uploadDocument,
  type Document,
  type Organization,
} from "../api/client";

const DOCUMENT_TYPES = [
  "contract",
  "regulation",
  "template",
  "tender",
  "policy",
  "other",
];

export default function RepositoryPage() {
  const { token } = useAuth();
  const [org, setOrg] = useState<Organization | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [title, setTitle] = useState("");
  const [docType, setDocType] = useState("contract");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");

  const load = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const orgs = await listOrganizations(token);
      const first = orgs.items[0];
      if (!first) return;
      setOrg(first);
      const docs = await listDocuments(token, first.id);
      setDocuments(docs.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, [token]);

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!token || !org || !file || !title) return;
    setUploading(true);
    setError("");
    try {
      await uploadDocument(token, org.id, file, title, docType);
      setTitle("");
      setFile(null);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId: string) => {
    if (!token || !org || !confirm("Delete this document?")) return;
    await deleteDocument(token, org.id, docId);
    await load();
  };

  const formatSize = (bytes?: number) => {
    if (!bytes) return "—";
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h2>Document Repository</h2>
          <p>{org ? org.name : "Loading organization..."}</p>
        </div>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <section className="card upload-card">
        <h3>Upload Document</h3>
        <form onSubmit={handleUpload} className="upload-form">
          <label>
            Title
            <input value={title} onChange={(e) => setTitle(e.target.value)} required />
          </label>
          <label>
            Type
            <select value={docType} onChange={(e) => setDocType(e.target.value)}>
              {DOCUMENT_TYPES.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <label>
            File
            <input
              type="file"
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
              required
            />
          </label>
          <button type="submit" className="btn-primary" disabled={uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </button>
        </form>
      </section>

      <section className="card">
        <h3>Documents ({documents.length})</h3>
        {loading ? (
          <p>Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="empty">No documents yet. Upload your first legal document.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Title</th>
                <th>Type</th>
                <th>Status</th>
                <th>File</th>
                <th>Size</th>
                <th>Created</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id}>
                  <td>{doc.title}</td>
                  <td>
                    <span className="badge">{doc.document_type}</span>
                  </td>
                  <td>
                    <span className={`status status-${doc.status}`}>{doc.status}</span>
                  </td>
                  <td>{doc.current_version?.file_name ?? "—"}</td>
                  <td>{formatSize(doc.current_version?.file_size)}</td>
                  <td>{new Date(doc.created_at).toLocaleString()}</td>
                  <td>
                    <button
                      type="button"
                      className="btn-danger-sm"
                      onClick={() => handleDelete(doc.id)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
