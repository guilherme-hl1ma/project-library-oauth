// frontend/client/app/routes.ts
import {
  type RouteConfig,
  index,
  route,
  layout,
} from "@react-router/dev/routes";

export default [
  // OAuth Flow Routes
  route("/login", "routes/login.tsx"),
  route("/oauth/authorize", "routes/oauth-authorize.tsx"),
  route("/oauth/callback", "routes/oauth-callback.tsx"),

  layout("layouts/auth-layout.tsx", [index("routes/home.tsx")]),
] satisfies RouteConfig;
