import { redirect, type LoaderFunctionArgs } from "react-router-dom";
import { apiFetch } from "~/controllers/api";

// layouts/auth-layout.tsx
export async function loader({ request }: LoaderFunctionArgs) {
  const cookieHeader = request.headers.get("Cookie");

  const response = await apiFetch("/users/me", {
    headers: {
      Cookie: cookieHeader || "",
    },
  });

  if (response.status === 401) {
    const url = new URL(request.url);
    throw redirect(`/login?next=${encodeURIComponent(url.pathname)}`);
  }

  return response.json();
}
