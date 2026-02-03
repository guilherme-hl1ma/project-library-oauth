// frontend/client/app/routes.ts
import {
  type RouteConfig,
  index,
  route,
  layout,
} from "@react-router/dev/routes";

export default [
  route("/login", "routes/login.tsx"),
  route("/callback", "routes/oauth-callback.tsx"),

  layout("layouts/auth-layout.tsx", [index("routes/home.tsx")]),
] satisfies RouteConfig;
