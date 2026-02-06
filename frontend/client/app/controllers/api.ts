export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const baseURL = "http://localhost:8000";
  const url = `${baseURL}${endpoint}`;

  let token = null;
  if (typeof window !== "undefined") {
    // Check for expiration via cookie existence (or parse it if we stored expiry)
    // Simple check: getCookie("access_token")
    
    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(";").shift();
      return null;
    };

    token = getCookie("access_token");

    if (!token) {
        // If strict mode is enforced and we are client-side, we might want to redirect.
        // But apiFetch is just a fetcher. Let it fail with 401 if no token.
        // Or if we want to enforce redirect here:
        // window.location.href = "/login";
        // keeping previous behavior of "if expired -> redirect", but cookie handles expiration automatically (browser removes it).
        
        // If we want to be explicit about expiration causing redirect:
        // Checking token existence usually implies validity.
    }
  }

  const defaultOptions: RequestInit = {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { "Authorization": `Bearer ${token}` } : {}),
      // No X-Token fallback
      ...options.headers,
    },
  };

  return await fetch(url, defaultOptions);
}
