import { redirect, type LoaderFunctionArgs } from "react-router-dom";
import { apiFetch } from "~/controllers/api";

// layouts/auth-layout.tsx
export async function loader({ request }: LoaderFunctionArgs) {
  // Client-side strict check for OAuth access_token
  // We need to ensure the user has completed the OAuth flow, not just the Backend Session login.
  if (typeof window !== "undefined") {
    const accessToken = localStorage.getItem("access_token");
    if (!accessToken) {
       const url = new URL(request.url);
       throw redirect(`/login?next=${encodeURIComponent(url.pathname)}`);
    }
  }

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

import { Outlet, useNavigate } from "react-router"; // Use react-router for Outlet/useNavigate in v7
import { useEffect } from "react";

export default function AuthLayout() {
  const navigate = useNavigate();

  useEffect(() => {
    // Strict Client Check:
    // Even if the server loader passed (via Cookie), we REQUIRE the access_token in COOKIES.
    // If it's missing, it means the Client isn't authorized for this app (OAuth flow not completed).
    
    const getCookie = (name: string) => {
      const value = `; ${document.cookie}`;
      const parts = value.split(`; ${name}=`);
      if (parts.length === 2) return parts.pop()?.split(";").shift();
      return null;
    };

    const accessToken = getCookie("access_token");
    if (!accessToken) {
      // Redirect to login to start the flow
      navigate("/login");
    }
  }, [navigate]);

  return <Outlet />;
}
