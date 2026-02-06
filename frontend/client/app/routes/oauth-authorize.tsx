import React from "react";

export default function Home() {
  const CLIENT_ID = import.meta.env.VITE_AUTH_CLIENT_ID;

  const AUTH_CONFIG = {
    url: "http://localhost:8000/authorize",
    client_id: CLIENT_ID,
    redirect_uri: "http://localhost:4000/oauth/callback",
    scope: "admin",
    state: "auth_request",
  };

  const handleLoginOAuth = () => {
    try {
      const token = localStorage.getItem("token");

      // Generate random state for CSRF protection
      const state = Math.random().toString(36).substring(7);
      sessionStorage.setItem("oauth_state", state);

      const params = new URLSearchParams({
        response_type: "code",
        client_id: AUTH_CONFIG.client_id,
        redirect_uri: window.location.origin + "/oauth/callback", // Use dynamic origin
        scope: AUTH_CONFIG.scope,
        state: state, // send generated state
      });

      if (!token) {
        console.log("No token, redirecting to login");
        const queryString = new URLSearchParams(params).toString();
        sessionStorage.setItem("oauth_return_params", `?${queryString}`);
        window.location.href = "/login";
        return;
      }

      const queryString = new URLSearchParams(params).toString();
      const url = `http://localhost:8000/authorize?${queryString}`;

      window.location.href = url;
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8 text-center">
        <h1 className="text-2xl font-bold text-gray-800 mb-4">
          Bem-vindo ao Client App
        </h1>
        <p className="text-gray-600 mb-8">
          Para acessar seus recursos protegidos, precisamos da sua autorização
          no servidor central.
        </p>

        <button
          onClick={handleLoginOAuth}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-200 ease-in-out transform hover:scale-105"
        >
          Autorizar com MyAuth Server
        </button>

        <div className="mt-6 text-sm text-gray-400">
          Você será redirecionado para o servidor de login com segurança.
        </div>
      </div>
    </div>
  );
}
