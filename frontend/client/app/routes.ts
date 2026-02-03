// frontend/client/app/routes.ts
import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("/login", "routes/login.tsx"),
  route("/callback", "routes/oauth-callback.tsx"),
] satisfies RouteConfig;
