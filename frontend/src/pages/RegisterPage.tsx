import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function RegisterPage() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await register(email, password);
      nav("/");
    } catch {
      setError("Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page auth-page">
      <div className="card">
        <h1>Tee Time Watcher</h1>
        <h2>Create account</h2>
        <form onSubmit={onSubmit}>
          <label>
            Email
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} required />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" disabled={loading}>
            {loading ? "Creating..." : "Create account"}
          </button>
        </form>
        <p>
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}

