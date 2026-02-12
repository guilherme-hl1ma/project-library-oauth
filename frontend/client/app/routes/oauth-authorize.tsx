import { useState } from "react";

const REQUESTED_SCOPES = ["read", "create", "update", "delete"];

export default function OAuthAuthorize() {
  const CLIENT_ID = import.meta.env.VITE_AUTH_CLIENT_ID;
  const [error, setError] = useState<string | null>(null);

  const handleLoginOAuth = () => {
    try {
      const state = crypto.randomUUID();
      sessionStorage.setItem("oauth_state", state);

      const params = new URLSearchParams({
        response_type: "code",
        client_id: CLIENT_ID,
        redirect_uri: window.location.origin + "/oauth/callback",
        scope: REQUESTED_SCOPES.join(" "),
        state: state,
      });

      const url = `http://localhost:8000/authorize?${params.toString()}`;
      window.location.href = url;
    } catch (err) {
      console.error(err);
      setError("Failed to start authorization flow.");
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <div style={styles.iconBox}>🚀</div>
          <h1 style={styles.title}>Bem-vindo ao Client App</h1>
          <p style={styles.subtitle}>
            Para acessar seus recursos protegidos, você precisa autorizar este
            aplicativo através do servidor de autenticação.
          </p>
        </div>

        <div style={styles.scopePreview}>
          <h3 style={styles.scopePreviewTitle}>
            Permissões que serão solicitadas:
          </h3>
          <ul style={styles.scopeList}>
            {REQUESTED_SCOPES.map((scope) => (
              <li key={scope} style={styles.scopeItem}>
                <span style={styles.scopeIcon}>✓</span>
                <span style={styles.scopeLabel}>{scope}</span>
              </li>
            ))}
          </ul>
          <p style={styles.scopeNote}>
            Você poderá revisar e aprovar estas permissões na próxima tela.
          </p>
        </div>

        {error && <p style={styles.errorText}>{error}</p>}

        <button onClick={handleLoginOAuth} style={styles.button}>
          Autorizar com MyAuth Server
        </button>

        <div style={styles.footerNote}>
          Você será redirecionado para o servidor de autenticação com segurança.
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
    padding: "20px",
    fontFamily: "'Inter', sans-serif",
  },
  card: {
    backgroundColor: "#ffffff",
    padding: "40px",
    borderRadius: "24px",
    boxShadow: "0 20px 60px rgba(0, 0, 0, 0.3)",
    width: "100%",
    maxWidth: "480px",
    textAlign: "center" as const,
  },
  header: {
    marginBottom: "32px",
  },
  iconBox: {
    width: "64px",
    height: "64px",
    backgroundColor: "#f7fafc",
    borderRadius: "16px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "32px",
    margin: "0 auto 20px auto",
  },
  title: {
    fontSize: "24px",
    fontWeight: "700",
    color: "#1a202c",
    margin: "0 0 10px 0",
  },
  subtitle: {
    fontSize: "15px",
    color: "#718096",
    lineHeight: "1.6",
    margin: 0,
  },
  scopePreview: {
    textAlign: "left" as const,
    backgroundColor: "#f8fafc",
    borderRadius: "12px",
    padding: "20px",
    marginBottom: "24px",
    border: "1px solid #edf2f7",
  },
  scopePreviewTitle: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#4a5568",
    margin: "0 0 12px 0",
  },
  scopeList: {
    listStyle: "none",
    padding: 0,
    margin: "0 0 12px 0",
    display: "flex",
    flexDirection: "column" as const,
    gap: "8px",
  },
  scopeItem: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  scopeIcon: {
    color: "#48bb78",
    fontWeight: "700",
    fontSize: "14px",
  },
  scopeLabel: {
    fontSize: "14px",
    color: "#2d3748",
    textTransform: "capitalize" as const,
  },
  scopeNote: {
    fontSize: "12px",
    color: "#a0aec0",
    margin: 0,
    fontStyle: "italic",
  },
  button: {
    width: "100%",
    padding: "16px",
    backgroundColor: "#667eea",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "600",
    transition: "all 0.2s",
    boxShadow: "0 10px 15px -3px rgba(102, 126, 234, 0.4)",
  },
  errorText: {
    color: "#e53e3e",
    fontSize: "14px",
    marginBottom: "20px",
  },
  footerNote: {
    marginTop: "20px",
    fontSize: "12px",
    color: "#a0aec0",
  },
};
