import { redirect, type LoaderFunctionArgs } from "react-router-dom";
import { Outlet } from "react-router";

function parseIdToken(cookieHeader: string | null): Record<string, any> | null {
  if (!cookieHeader) return null;

  const match = cookieHeader
    .split(";")
    .map((c) => c.trim())
    .find((c) => c.startsWith("id_token="));

  if (!match) return null;

  const token = match.split("=")[1];
  if (!token) return null;

  try {
    // JWT has 3 parts: header.payload.signature
    // We only need the payload (index 1)
    const payload = token.split(".")[1];
    const decoded = atob(payload.replace(/-/g, "+").replace(/_/g, "/"));
    const data = JSON.parse(decoded);

    // Check if token is expired
    if (data.exp && data.exp * 1000 < Date.now()) {
      return null;
    }

    return data;
  } catch {
    return null;
  }
}

export async function loader({ request }: LoaderFunctionArgs) {
  const cookieHeader = request.headers.get("Cookie");
  const user = parseIdToken(cookieHeader);

  if (!user) {
    throw redirect("/oauth/authorize");
  }

  return {
    sub: user.sub,
    email: user.email,
    role: user.role,
  };
}

export default function AuthLayout() {
  return <Outlet />;
}
