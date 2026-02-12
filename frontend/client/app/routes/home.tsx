import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { loader as authLoader } from "../layouts/auth-layout";
import { apiFetch } from "~/controllers/api";
import type { Route } from "./+types/home";

export const loader = authLoader;

export function meta({}: Route.MetaArgs) {
  return [
    { title: "Dashboard - Projects" },
    { name: "description", content: "Manage your projects" },
  ];
}

interface Project {
  id: string;
  name: string;
  description: string;
}

export default function Home({ loaderData }: Route.ComponentProps) {
  const user = loaderData;
  const navigate = useNavigate();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [newProject, setNewProject] = useState({ name: "", description: "" });
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [error, setError] = useState<string | null>(null);

  const fetchProjects = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiFetch("/projects/");
      if (response.ok) {
        setProjects(await response.json());
      } else if (response.status === 403) {
        setError("Scope Missing: You need 'read' scope to view projects.");
      } else {
        setError("Failed to fetch projects");
      }
    } catch (err) {
      setError("Network error fetching projects");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const handleCreateProject = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const response = await apiFetch("/projects/", {
        method: "POST",
        body: JSON.stringify(newProject),
      });
      if (response.ok) {
        setNewProject({ name: "", description: "" });
        fetchProjects();
      } else if (response.status === 403) {
        setError("Scope Missing: You need 'create' scope to add projects.");
      }
    } catch (err) {
      setError("Error creating project");
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingProject) return;
    setError(null);
    try {
      const response = await apiFetch(`/projects/${editingProject.id}`, {
        method: "PATCH",
        body: JSON.stringify({
          name: editingProject.name,
          description: editingProject.description,
        }),
      });
      if (response.ok) {
        setEditingProject(null);
        fetchProjects();
      } else if (response.status === 403) {
        setError("Scope Missing: You need 'update' scope to edit projects.");
      }
    } catch (err) {
      setError("Error updating project");
    }
  };

  const handleDelete = async (id: string) => {
    setError(null);
    try {
      const response = await apiFetch(`/projects/${id}`, { method: "DELETE" });
      if (response.ok) {
        fetchProjects();
      } else if (response.status === 403) {
        setError("Scope Missing: You need 'delete' scope to remove projects.");
      }
    } catch (err) {
      setError("Error deleting project");
    }
  };

  const handleLogout = async () => {
    await apiFetch("/token/revoke", { method: "POST" }, false);
    sessionStorage.removeItem("oauth_return_params");
    window.location.href = "http://localhost:3000/login";
  };

  const handleDeauthorize = async () => {
    await apiFetch("/token/revoke-consent", { method: "POST" }, false);
    sessionStorage.removeItem("oauth_return_params");
    navigate("/oauth/authorize");
  };

  return (
    <div style={styles.container}>
      <div style={styles.sidebar}>
        <div style={styles.userSection}>
          <div style={styles.avatar}>
            {user.email ? user.email[0].toUpperCase() : "U"}
          </div>
          <div style={styles.userText}>
            <p style={styles.userEmail}>{user.email}</p>
            <p style={styles.userRole}>{user.role}</p>
          </div>
        </div>
        <div style={styles.sidebarActions}>
          <button onClick={handleDeauthorize} style={styles.deauthButton}>
            Desautorizar
          </button>
          <button onClick={handleLogout} style={styles.logoutButton}>
            Logout
          </button>
        </div>
      </div>

      <div style={styles.mainContent}>
        <div style={styles.card}>
          <div style={styles.header}>
            <h1 style={styles.title}>Project Dashboard</h1>
            <p style={styles.subtitle}>Manage your protected resources</p>
          </div>

          {error && (
            <div style={styles.errorBox}>
              <span style={styles.errorText}>{error}</span>
              <button onClick={() => setError(null)} style={styles.errorClose}>
                ×
              </button>
            </div>
          )}

          <section style={styles.formSection}>
            <h2 style={styles.sectionTitle}>
              {editingProject ? "Edit Project" : "Create New Project"}
            </h2>
            <form
              onSubmit={editingProject ? handleUpdate : handleCreateProject}
              style={styles.form}
            >
              <input
                placeholder="Project Name"
                value={editingProject ? editingProject.name : newProject.name}
                onChange={(e) =>
                  editingProject
                    ? setEditingProject({
                        ...editingProject,
                        name: e.target.value,
                      })
                    : setNewProject({ ...newProject, name: e.target.value })
                }
                style={styles.input}
                required
              />
              <textarea
                placeholder="Description"
                value={
                  editingProject
                    ? editingProject.description
                    : newProject.description
                }
                onChange={(e) =>
                  editingProject
                    ? setEditingProject({
                        ...editingProject,
                        description: e.target.value,
                      })
                    : setNewProject({
                        ...newProject,
                        description: e.target.value,
                      })
                }
                style={{ ...styles.input, minHeight: "80px" }}
              />
              <div style={styles.formActions}>
                <button type="submit" style={styles.primaryButton}>
                  {editingProject ? "Update Project" : "Add Project"}
                </button>
                {editingProject && (
                  <button
                    type="button"
                    onClick={() => setEditingProject(null)}
                    style={styles.secondaryButton}
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </section>

          <section style={styles.listSection}>
            <h2 style={styles.sectionTitle}>Your Projects</h2>
            {loading ? (
              <p style={styles.loadingText}>Fetching projects...</p>
            ) : projects.length === 0 ? (
              <p style={styles.emptyText}>
                No projects found. Use your 'create' scope to add one!
              </p>
            ) : (
              <div style={styles.projectList}>
                {projects.map((project) => (
                  <div key={project.id} style={styles.projectItem}>
                    <div style={styles.projectInfo}>
                      <h3 style={styles.projectName}>{project.name}</h3>
                      <p style={styles.projectDesc}>{project.description}</p>
                    </div>
                    <div style={styles.projectActions}>
                      <button
                        onClick={() => setEditingProject(project)}
                        style={styles.actionButton}
                        title="Edit"
                      >
                        ✏️
                      </button>
                      <button
                        onClick={() => handleDelete(project.id)}
                        style={{ ...styles.actionButton, color: "#e53e3e" }}
                        title="Delete"
                      >
                        🗑️
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

const styles = {
  container: {
    display: "flex",
    minHeight: "100vh",
    backgroundColor: "#f7fafc",
    fontFamily: "'Inter', sans-serif",
  },
  sidebar: {
    width: "280px",
    backgroundColor: "#2d3748",
    padding: "32px 24px",
    display: "flex",
    flexDirection: "column" as const,
    justifyContent: "space-between",
    color: "#ffffff",
  },
  userSection: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
  },
  avatar: {
    width: "40px",
    height: "40px",
    borderRadius: "50%",
    backgroundColor: "#667eea",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "18px",
    fontWeight: "600",
  },
  userText: {
    overflow: "hidden",
  },
  userEmail: {
    margin: 0,
    fontSize: "14px",
    fontWeight: "600",
    whiteSpace: "nowrap" as const,
    overflow: "hidden",
    textOverflow: "ellipsis",
  },
  userRole: {
    margin: 0,
    fontSize: "12px",
    color: "#a0aec0",
    textTransform: "uppercase" as const,
  },
  logoutButton: {
    padding: "12px",
    backgroundColor: "transparent",
    border: "1px solid #4a5568",
    borderRadius: "8px",
    color: "#ffffff",
    cursor: "pointer",
    fontSize: "14px",
    fontWeight: "500",
    transition: "all 0.2s",
  },
  deauthButton: {
    padding: "12px",
    backgroundColor: "transparent",
    border: "1px solid #e53e3e",
    borderRadius: "8px",
    color: "#fc8181",
    cursor: "pointer",
    fontSize: "13px",
    fontWeight: "500",
    transition: "all 0.2s",
  },
  sidebarActions: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "8px",
    marginTop: "auto",
  },
  mainContent: {
    flex: 1,
    padding: "40px",
    display: "flex",
    justifyContent: "center",
    overflowY: "auto" as const,
  },
  card: {
    backgroundColor: "#ffffff",
    padding: "40px",
    borderRadius: "20px",
    boxShadow: "0 10px 25px rgba(0, 0, 0, 0.05)",
    width: "100%",
    maxWidth: "800px",
    height: "fit-content",
  },
  header: {
    marginBottom: "40px",
    textAlign: "center" as const,
  },
  title: {
    fontSize: "32px",
    fontWeight: "800",
    color: "#1a202c",
    margin: "0 0 8px 0",
  },
  subtitle: {
    fontSize: "16px",
    color: "#718096",
    margin: 0,
  },
  errorBox: {
    backgroundColor: "#fff5f5",
    border: "1px solid #fed7d7",
    color: "#c53030",
    padding: "12px 16px",
    borderRadius: "8px",
    marginBottom: "24px",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    fontSize: "14px",
  },
  errorText: {
    fontWeight: "500",
  },
  errorClose: {
    background: "none",
    border: "none",
    color: "#c53030",
    fontSize: "18px",
    cursor: "pointer",
  },
  sectionTitle: {
    fontSize: "20px",
    fontWeight: "700",
    color: "#2d3748",
    marginBottom: "20px",
    borderBottom: "2px solid #edf2f7",
    paddingBottom: "8px",
  },
  formSection: {
    marginBottom: "48px",
  },
  form: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "16px",
  },
  input: {
    padding: "12px 16px",
    border: "1px solid #e2e8f0",
    borderRadius: "8px",
    fontSize: "16px",
    outline: "none",
    transition: "border-color 0.2s",
  },
  formActions: {
    display: "flex",
    gap: "12px",
  },
  primaryButton: {
    padding: "12px 24px",
    backgroundColor: "#667eea",
    color: "#ffffff",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "600",
    transition: "background 0.2s",
  },
  secondaryButton: {
    padding: "12px 24px",
    backgroundColor: "#edf2f7",
    color: "#4a5568",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    fontSize: "16px",
    fontWeight: "600",
  },
  listSection: {},
  projectList: {
    display: "flex",
    flexDirection: "column" as const,
    gap: "16px",
  },
  projectItem: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "20px",
    backgroundColor: "#f8fafc",
    borderRadius: "12px",
    border: "1px solid #edf2f7",
  },
  projectInfo: {
    flex: 1,
  },
  projectName: {
    fontSize: "18px",
    fontWeight: "700",
    color: "#2d3748",
    margin: "0 0 4px 0",
  },
  projectDesc: {
    fontSize: "14px",
    color: "#718096",
    margin: 0,
  },
  projectActions: {
    display: "flex",
    gap: "8px",
  },
  actionButton: {
    background: "none",
    border: "none",
    fontSize: "18px",
    cursor: "pointer",
    padding: "8px",
    borderRadius: "6px",
    transition: "background 0.2s",
  },
  loadingText: {
    textAlign: "center" as const,
    color: "#718096",
    padding: "40px",
  },
  emptyText: {
    textAlign: "center" as const,
    color: "#718096",
    padding: "40px",
    fontStyle: "italic",
  },
};
