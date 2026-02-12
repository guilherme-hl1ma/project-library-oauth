// frontend/auth-frontend/app/routes.ts
import { type RouteConfig, index, route } from "@react-router/dev/routes";

export default [
  index("routes/home.tsx"),
  route("/login", "routes/login.tsx"),
  route("/consent", "routes/consent.tsx"),
] satisfies RouteConfig;
