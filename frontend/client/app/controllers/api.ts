export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const baseURL = "http://localhost:8000";
  const url = `${baseURL}${endpoint}`;

  let token = null;
  if (typeof window !== "undefined") {
    token = localStorage.getItem("token");
  }

  const defaultOptions: RequestInit = {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "X-Token": token } : {}),
      ...options.headers,
    },
  };

  return await fetch(url, defaultOptions);
}
