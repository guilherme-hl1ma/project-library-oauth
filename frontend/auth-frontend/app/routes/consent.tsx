import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import type { Route } from "./+types/consent";

const AUTH_SERVER_URL = "http://localhost:8000";

interface ConsentData {
  client_name: string;
  scopes: string[];
  user_email: string;
}

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Authorize Application" },
    { name: "description", content: "Review and approve application access" },
  ];
}

export default function Consent() {
  const [consentData, setConsentData] = useState<ConsentData | null>(null);
  const [selectedScopes, setSelectedScopes] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const params = new URLSearchParams(
    typeof window !== "undefined" ? window.location.search : "",
  );
  const consentId = params.get("consent_id");

  useEffect(() => {
    if (!consentId) {
      setError(
        "Missing consent request. Please start the authorization flow again.",
      );
      setLoading(false);
      return;
    }

    fetch(`${AUTH_SERVER_URL}/authorize/consent-data?consent_id=${consentId}`, {
      credentials: "include",
    })
      .then(async (res) => {
        if (!res.ok) {
          if (res.status === 401) {
            window.location.href = `/login?return_to=${encodeURIComponent(
              window.location.pathname + window.location.search,
            )}`;
            return;
          }
          throw new Error("Failed to load consent data");
        }
        return res.json();
      })
      .then((data: ConsentData | undefined) => {
        if (data) {
          setConsentData(data);
          setSelectedScopes(data.scopes);
        }
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [consentId]);

  const toggleScope = (scope: string) => {
    setSelectedScopes((prev) =>
      prev.includes(scope) ? prev.filter((s) => s !== scope) : [...prev, scope],
    );
  };

  const handleApprove = async () => {
    if (!consentId) return;
    setSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${AUTH_SERVER_URL}/authorize/consent`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consent_id: consentId,
          approved: true,
          approved_scopes: selectedScopes,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to approve consent");
      }

      const data = await res.json();
      window.location.href = data.redirect_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setSubmitting(false);
    }
  };

  const handleDeny = async () => {
    if (!consentId) return;
    setSubmitting(true);

    try {
      const res = await fetch(`${AUTH_SERVER_URL}/authorize/consent`, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          consent_id: consentId,
          approved: false,
          approved_scopes: [],
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to process denial");
      }

      const data = await res.json();
      window.location.href = data.redirect_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
      setSubmitting(false);
    }
  };

  const SCOPE_DESCRIPTIONS: Record<
    string,
    { label: string; description: string; icon: string }
  > = {
    read: {
      label: "Read",
      description: "Visualizar seus projetos e detalhes",
      icon: "📖",
    },
    create: {
      label: "Create",
      description: "Criar novos projetos em seu nome",
      icon: "➕",
    },
    update: {
      label: "Update",
      description: "Editar e modificar seus projetos",
      icon: "✏️",
    },
    delete: {
      label: "Delete",
      description: "Excluir projetos permanentemente",
      icon: "🗑️",
    },
  };

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.loading}>
            <div style={styles.spinner}>🔄</div>
            <p style={styles.loadingText}>Loading authorization request...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !consentData) {
    return (
      <div style={styles.container}>
        <div style={styles.card}>
          <div style={styles.errorContainer}>
            <div style={styles.errorIcon}>⚠️</div>
            <h2 style={styles.errorTitle}>Authorization Error</h2>
            <p style={styles.errorMessage}>{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        {/* Header */}
        <div style={styles.header}>
          <div style={styles.shieldIcon}>🛡️</div>
          <h1 style={styles.title}>Autorizar Aplicação</h1>
          <p style={styles.subtitle}>
            <strong style={styles.clientName}>
              {consentData?.client_name}
            </strong>{" "}
            está solicitando acesso à sua conta
          </p>
        </div>

        {/* User info */}
        <div style={styles.userCard}>
          <div style={styles.userAvatar}>
            {consentData?.user_email?.[0]?.toUpperCase() || "U"}
          </div>
          <div style={styles.userInfo}>
            <span style={styles.userLabel}>Logado como</span>
            <span style={styles.userEmail}>{consentData?.user_email}</span>
          </div>
        </div>

        {/* Scopes */}
        <div style={styles.scopesSection}>
          <h3 style={styles.scopesTitle}>Permissões solicitadas:</h3>
          <div style={styles.scopesList}>
            {consentData?.scopes.map((scope) => {
              const info = SCOPE_DESCRIPTIONS[scope] || {
                label: scope,
                description: "",
                icon: "🔑",
              };
              return (
                <label
                  key={scope}
                  style={{
                    ...styles.scopeItem,
                    ...(selectedScopes.includes(scope)
                      ? styles.scopeItemSelected
                      : {}),
                  }}
                  onClick={(e) => {
                    if ((e.target as HTMLElement).tagName === "INPUT") return;
                    toggleScope(scope);
                  }}
                >
                  <div style={styles.scopeLeft}>
                    <span style={styles.scopeEmoji}>{info.icon}</span>
                    <div style={styles.scopeInfo}>
                      <span style={styles.scopeLabel}>{info.label}</span>
                      <span style={styles.scopeDesc}>{info.description}</span>
                    </div>
                  </div>
                  <input
                    type="checkbox"
                    checked={selectedScopes.includes(scope)}
                    onChange={() => toggleScope(scope)}
                    style={styles.checkbox}
                  />
                </label>
              );
            })}
          </div>
        </div>

        {error && <p style={styles.inlineError}>{error}</p>}

        {/* Actions */}
        <div style={styles.actions}>
          <button
            onClick={handleApprove}
            disabled={submitting || selectedScopes.length === 0}
            style={{
              ...styles.approveButton,
              ...(submitting || selectedScopes.length === 0
                ? styles.buttonDisabled
                : {}),
            }}
          >
            {submitting ? "Processando..." : "Autorizar"}
          </button>
          <button
            onClick={handleDeny}
            disabled={submitting}
            style={{
              ...styles.denyButton,
              ...(submitting ? styles.buttonDisabled : {}),
            }}
          >
            Negar
          </button>
        </div>

        <p style={styles.footerNote}>
          Ao autorizar, você permite que esta aplicação acesse seus recursos de
          acordo com as permissões selecionadas.
        </p>
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
    padding: "40px",
    borderRadius: "24px",
    boxShadow: "0 25px 80px rgba(0, 0, 0, 0.4)",
    width: "100%",
    maxWidth: "520px",
  },
  loading: {
    textAlign: "center",
    padding: "40px 0",
  },
  spinner: {
    fontSize: "48px",
    animation: "spin 2s linear infinite",
  },
  loadingText: {
    color: "#718096",
    fontSize: "16px",
    marginTop: "16px",
  },
  errorContainer: {
    textAlign: "center",
    padding: "20px 0",
  },
  errorIcon: {
    fontSize: "48px",
    marginBottom: "16px",
  },
  errorTitle: {
    fontSize: "22px",
    fontWeight: "700",
    color: "#c53030",
    margin: "0 0 8px 0",
  },
  errorMessage: {
    fontSize: "14px",
    color: "#718096",
  },
  header: {
    textAlign: "center",
    marginBottom: "28px",
  },
  shieldIcon: {
    fontSize: "48px",
    marginBottom: "16px",
  },
  title: {
    fontSize: "24px",
    fontWeight: "800",
    color: "#1a202c",
    margin: "0 0 10px 0",
  },
  subtitle: {
    fontSize: "15px",
    color: "#718096",
    lineHeight: "1.6",
    margin: 0,
  },
  clientName: {
    color: "#4c51bf",
    fontWeight: "700",
  },
  userCard: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "14px 18px",
    backgroundColor: "#f0f4ff",
    borderRadius: "12px",
    marginBottom: "24px",
    border: "1px solid #c3dafe",
  },
  userAvatar: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    backgroundColor: "#667eea",
    color: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
    fontWeight: "700",
    flexShrink: 0,
  },
  userInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
  },
  userLabel: {
    fontSize: "11px",
    color: "#a0aec0",
    textTransform: "uppercase",
    fontWeight: "600",
    letterSpacing: "0.5px",
  },
  userEmail: {
    fontSize: "14px",
    color: "#2d3748",
    fontWeight: "600",
  },
  scopesSection: {
    marginBottom: "24px",
  },
  scopesTitle: {
    fontSize: "14px",
    fontWeight: "700",
    color: "#4a5568",
    margin: "0 0 14px 0",
    textTransform: "uppercase",
    letterSpacing: "0.5px",
  },
  scopesList: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  },
  scopeItem: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "14px 16px",
    backgroundColor: "#f8fafc",
    borderRadius: "12px",
    border: "2px solid #edf2f7",
    cursor: "pointer",
    transition: "all 0.2s ease",
  },
  scopeItemSelected: {
    borderColor: "#667eea",
    backgroundColor: "#f0f4ff",
  },
  scopeLeft: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  scopeEmoji: {
    fontSize: "20px",
  },
  scopeInfo: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
  },
  scopeLabel: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#2d3748",
  },
  scopeDesc: {
    fontSize: "12px",
    color: "#718096",
  },
  checkbox: {
    width: "20px",
    height: "20px",
    cursor: "pointer",
    accentColor: "#667eea",
  },
  inlineError: {
    color: "#e53e3e",
    fontSize: "14px",
    marginBottom: "16px",
    textAlign: "center",
  },
  actions: {
    display: "flex",
    gap: "12px",
    marginBottom: "16px",
  },
  approveButton: {
    flex: 2,
    padding: "14px",
    backgroundColor: "#48bb78",
    color: "#ffffff",
    border: "none",
    borderRadius: "12px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "700",
    transition: "all 0.2s",
    boxShadow: "0 8px 15px -3px rgba(72, 187, 120, 0.4)",
  },
  denyButton: {
    flex: 1,
    padding: "14px",
    backgroundColor: "#ffffff",
    color: "#e53e3e",
    border: "2px solid #fed7d7",
    borderRadius: "12px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "600",
    transition: "all 0.2s",
  },
  buttonDisabled: {
    opacity: 0.5,
    cursor: "not-allowed",
  },
  footerNote: {
    fontSize: "12px",
    color: "#a0aec0",
    textAlign: "center",
    lineHeight: "1.5",
  },
};
