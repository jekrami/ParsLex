import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { listAuditEvents, listOrganizations, type AuditEvent } from "../api/client";

export default function AuditPage() {
  const { token } = useAuth();
  const [events, setEvents] = useState<AuditEvent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) return;
    (async () => {
      const orgs = await listOrganizations(token);
      const org = orgs.items[0];
      if (!org) return;
      const res = await listAuditEvents(token, org.id);
      setEvents(res.items);
      setLoading(false);
    })();
  }, [token]);

  return (
    <div className="page">
      <div className="page-header">
        <h2>Audit Trail</h2>
        <p>Immutable log of platform actions</p>
      </div>

      <section className="card">
        {loading ? (
          <p>Loading audit events...</p>
        ) : events.length === 0 ? (
          <p className="empty">No audit events recorded yet.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Time</th>
                <th>Action</th>
                <th>Resource</th>
                <th>User</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              {events.map((e) => (
                <tr key={e.id}>
                  <td>{new Date(e.created_at).toLocaleString()}</td>
                  <td>
                    <span className="badge">{e.action}</span>
                  </td>
                  <td>{e.resource_type}</td>
                  <td>{e.user_email ?? "—"}</td>
                  <td className="metadata-cell">
                    {Object.keys(e.metadata).length > 0
                      ? JSON.stringify(e.metadata)
                      : "—"}
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
