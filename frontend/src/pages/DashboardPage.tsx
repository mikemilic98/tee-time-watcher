import { useAuth } from "../auth/AuthContext";

export function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <div className="page dashboard-page">
      <header className="topbar">
        <div className="brand">Tee Time Watcher</div>
        <div className="spacer" />
        <div className="user-info">
          <span>{user?.email}</span>
          <button onClick={logout}>Sign out</button>
        </div>
      </header>
      <main className="layout">
        <section className="panel">
          <h2>Your watch rules</h2>
          <p>Watch rule management UI will go here (course selector, date/time, price filters).</p>
        </section>
        <section className="panel">
          <h2>Upcoming tee time candidates</h2>
          <p>List of detected tee times and booking status will appear here.</p>
        </section>
        <section className="panel">
          <h2>Notifications</h2>
          <p>In-app notifications about bookings and cancellations will appear here.</p>
        </section>
      </main>
    </div>
  );
}

