const BASE_URL = "http://localhost:8000";

let isRefreshing = false;
let refreshPromise: Promise<boolean> | null = null;

async function refreshAccessToken(): Promise<boolean> {
  if (isRefreshing && refreshPromise) {
    return refreshPromise;
  }

  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      const response = await fetch(`${BASE_URL}/token`, {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          grant_type: "refresh_token",
        }),
      });

      return response.ok;
    } catch (error) {
      console.error("Error refreshing token:", error);
      return false;
    } finally {
      isRefreshing = false;
      refreshPromise = null;
    }
  })();

  return refreshPromise;
}

export async function apiFetch(
  endpoint: string,
  options: RequestInit = {},
  retryOnUnauthorized: boolean = true
): Promise<Response> {
  const defaultOptions: RequestInit = {
    credentials: "include",
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  const url = `${BASE_URL}${endpoint}`;
  const response = await fetch(url, defaultOptions);

  if (response.status === 401 && retryOnUnauthorized) {
    const refreshed = await refreshAccessToken();

    if (refreshed) {
      return await fetch(url, defaultOptions);
    }
  }

  return response;
}
