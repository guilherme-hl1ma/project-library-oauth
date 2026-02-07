import { redirect, type LoaderFunctionArgs } from "react-router-dom";
import { apiFetch } from "~/controllers/api";

export async function loader({ request }: LoaderFunctionArgs) {
  const cookieHeader = request.headers.get("Cookie");

  const response = await apiFetch("/auth/me", {
    headers: {
      Cookie: cookieHeader || "",
    },
  });

  if (response.status === 401) {
    throw redirect("/oauth/authorize");
  }

  return response.json();
}

import { Outlet } from "react-router";

export default function AuthLayout() {
  return <Outlet />;
}
