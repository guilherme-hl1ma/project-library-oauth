import { useNavigate } from "react-router";
import { loader as authLoader } from "../layouts/auth-layout";
import type { Route } from "./+types/home";

export const loader = authLoader;

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Home" },
    { name: "description", content: "Welcome to your dashboard" },
  ];
}

export default function Home({ loaderData }: Route.ComponentProps) {
  const user = loaderData;
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("token");
    // Also clear any other stored auth data if necessary
    sessionStorage.removeItem("oauth_return_params");
    navigate("/login");
  };

  return (
    <div style={styles.container}>
      <div style={styles.card}>
        <div style={styles.header}>
          <h1 style={styles.title}>Welcome!</h1>
          <p style={styles.subtitle}>You are successfully logged in</p>
        </div>

        <div style={styles.content}>
          <div style={styles.userInfo}>
            <div style={styles.avatarPlaceholder}>
              {user.email ? user.email[0].toUpperCase() : "U"}
            </div>
            <div style={styles.userDetails}>
              <p style={styles.userEmail}>{user.email || "User"}</p>
              <p style={styles.userId}>ID: {user.id}</p>
            </div>
          </div>

          <button onClick={handleLogout} style={styles.button}>
            Logout
          </button>
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
  },
  card: {
    backgroundColor: "#ffffff",
    padding: "48px",
    borderRadius: "16px",
    boxShadow: "0 20px 60px rgba(0, 0, 0, 0.3)",
    width: "100%",
    maxWidth: "440px",
  },
  header: {
    marginBottom: "32px",
    textAlign: "center" as const,
  },
  title: {
    fontSize: "28px",
    fontWeight: "700",
    color: "#1a202c",
    margin: "0 0 8px 0",
  },
  subtitle: {
    fontSize: "14px",
    color: "#718096",
    margin: 0,
  },
  content: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "24px",
  },
  userInfo: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    padding: "16px",
    backgroundColor: "#f7fafc",
    borderRadius: "12px",
    border: "1px solid #edf2f7",
  },
  avatarPlaceholder: {
    width: "48px",
    height: "48px",
    borderRadius: "50%",
    backgroundColor: "#667eea",
    color: "#ffffff",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "20px",
    fontWeight: "600",
  },
  userDetails: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "4px",
  },
  userEmail: {
    fontSize: "16px",
    fontWeight: "600",
    color: "#2d3748",
    margin: 0,
  },
  userId: {
    fontSize: "12px",
    color: "#718096",
    margin: 0,
    fontFamily: "monospace",
  },
  button: {
    padding: "14px",
    backgroundColor: "#DC2626", // Red for logout
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "600",
    transition: "all 0.2s",
    width: "100%",
  },
};
