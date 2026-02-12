import { useState } from "react";
import type { Route } from "./+types/login";

const AUTH_SERVER_URL = "http://localhost:8000";

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Login - Auth Server" },
    { name: "description", content: "Sign in to your account" },
  ];
}

export default function Login() {
  const [credentials, setCredentials] = useState({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${AUTH_SERVER_URL}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
        credentials: "include",
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Login failed");
      }

      const params = new URLSearchParams(window.location.search);
      const returnTo = params.get("return_to");
      const oauthParams = params.get("oauth_params");

      if (returnTo && oauthParams) {
        window.location.href = `${AUTH_SERVER_URL}${returnTo}?${oauthParams}`;
      } else if (returnTo) {
        window.location.href = returnTo;
      } else {
        window.location.href = "/";
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div style={styles.lockIcon}>🔐</div>
          <h1 style={styles.title}>Auth Server</h1>
          <p style={styles.subtitle}>Sign in to continue</p>
        </div>

        {error && (
          <div style={styles.errorBox}>
            <span style={styles.errorEmoji}>⚠️</span>
            <p style={styles.errorText}>{error}</p>
          </div>
        )}

        <form onSubmit={handleLogin} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Email</label>
            <input
              type="email"
              placeholder="you@example.com"
              value={credentials.email}
              onChange={(e) =>
                setCredentials({ ...credentials, email: e.target.value })
              }
              style={styles.input}
              required
            />
          </div>

          <div style={styles.inputGroup}>
            <label style={styles.label}>Password</label>
            <input
              type="password"
              placeholder="••••••••"
              value={credentials.password}
              onChange={(e) =>
                setCredentials({ ...credentials, password: e.target.value })
              }
              style={styles.input}
              required
            />
          </div>

          <button
            type="submit"
            style={{
              ...styles.button,
              ...(loading ? styles.buttonDisabled : {}),
            }}
            disabled={loading}
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    background:
      "linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%)",
    padding: "20px",
    fontFamily: "'Inter', sans-serif",
  },
  card: {
    backgroundColor: "#ffffff",
    padding: "48px",
    borderRadius: "24px",
    boxShadow: "0 25px 80px rgba(0, 0, 0, 0.4)",
    width: "100%",
    maxWidth: "440px",
  },
  header: {
    textAlign: "center",
    marginBottom: "32px",
  },
  lockIcon: {
    fontSize: "48px",
    marginBottom: "12px",
  },
  title: {
    fontSize: "28px",
    fontWeight: "800",
    color: "#1a202c",
    margin: "0 0 6px 0",
  },
  subtitle: {
    fontSize: "14px",
    color: "#718096",
    margin: 0,
  },
  errorBox: {
    backgroundColor: "#FEE2E2",
    border: "1px solid #FCA5A5",
    borderRadius: "10px",
    padding: "12px 16px",
    marginBottom: "24px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
  },
  errorEmoji: {
    fontSize: "18px",
    flexShrink: 0,
  },
  errorText: {
    color: "#991B1B",
    fontSize: "14px",
    margin: 0,
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "20px",
  },
  inputGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  label: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#374151",
  },
  input: {
    padding: "12px 16px",
    border: "2px solid #e5e7eb",
    borderRadius: "10px",
    fontSize: "16px",
    transition: "all 0.2s",
    outline: "none",
    backgroundColor: "#ffffff",
    color: "#1a202c",
  },
  button: {
    padding: "14px",
    backgroundColor: "#4c51bf",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "700",
    transition: "all 0.2s",
    marginTop: "8px",
    boxShadow: "0 8px 15px -3px rgba(76, 81, 191, 0.4)",
  },
  buttonDisabled: {
    backgroundColor: "#9ca3af",
    cursor: "not-allowed",
    boxShadow: "none",
  },
};
