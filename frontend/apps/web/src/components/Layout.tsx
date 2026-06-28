import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export default function Layout() {
  const { user, logout } = useAuth();

  return (
    <div className="layout">
      <header className="header">
        <div className="brand">
          <span className="brand-mark">PL</span>
          <div>
            <h1>ParsLex</h1>
            <p>Enterprise Legal AI Platform</p>
          </div>
        </div>
        <nav className="nav">
          <NavLink to="/" end>
            Repository
          </NavLink>
          <NavLink to="/audit">Audit Trail</NavLink>
        </nav>
        <div className="user-bar">
          <span>{user?.full_name}</span>
          <button type="button" onClick={logout} className="btn-secondary">
            Logout
          </button>
        </div>
      </header>
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
