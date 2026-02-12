import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("Initializing...");
  const [error, setError] = useState<string | null>(null);
  const [countdown, setCountdown] = useState<number | null>(null);
  const [redirectPath, setRedirectPath] = useState<string>("/");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");
    const errorParam = params.get("error");
    const errorDescription = params.get("error_description");
    const state = params.get("state");

    const savedState = sessionStorage.getItem("oauth_state");
    if (state !== savedState) {
      setError("Security Error: State mismatch (CSRF protection)");
      setStatus("Authorization failed");
      setRedirectPath("/login");
      setCountdown(3);
      return;
    }
    sessionStorage.removeItem("oauth_state");

    if (errorParam) {
      let errorMessage = "";
      let shouldRetryAuth = false;

      switch (errorParam) {
        case "invalid_request":
          errorMessage = "Invalid request: implementation error.";
          shouldRetryAuth = false;
          break;
        case "unauthorized_client":
          errorMessage = "Unauthorized client configuration.";
          shouldRetryAuth = false;
          break;
        case "access_denied":
          errorMessage = "Access denied: You denied the authorization request.";
          shouldRetryAuth = true;
          break;
        case "unsupported_response_type":
          errorMessage = "Unsupported response type.";
          shouldRetryAuth = false;
          break;
        case "invalid_scope":
          errorMessage = "Invalid scope requested.";
          shouldRetryAuth = false;
          break;
        case "server_error":
          errorMessage = "Server error from authorization server.";
          shouldRetryAuth = true;
          break;
        case "temporarily_unavailable":
          errorMessage = "Authorization server temporarily unavailable.";
          shouldRetryAuth = true;
          break;
        default:
          errorMessage = `Unknown error: ${errorParam}`;
          shouldRetryAuth = false;
      }

      if (errorDescription) {
        errorMessage = decodeURIComponent(errorDescription);
      }

      setError(errorMessage);
      setStatus("Authorization failed");

      const path = shouldRetryAuth ? "/oauth/authorize" : "/login";
      setRedirectPath(path);
      setCountdown(5);
      return;
    }

    if (!code) {
      setError("No authorization code received");
      setStatus("Authorization failed");
      setRedirectPath("/login");
      setCountdown(3);
      return;
    }

    setStatus("Exchanging code for token...");

    const clientId = import.meta.env.VITE_AUTH_CLIENT_ID;

    // PKCE: retrieve the code_verifier generated before the authorization request
    const codeVerifier = sessionStorage.getItem("pkce_code_verifier");
    sessionStorage.removeItem("pkce_code_verifier");

    if (!codeVerifier) {
      setError("PKCE Error: code_verifier not found. Please restart the flow.");
      setStatus("Authorization failed");
      setRedirectPath("/oauth/authorize");
      setCountdown(3);
      return;
    }

    const body = {
      grant_type: "authorization_code",
      code: code,
      redirect_uri: window.location.origin + "/oauth/callback",
      client_id: clientId,
      code_verifier: codeVerifier,
    };

    fetch("http://localhost:8000/token", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      credentials: "include",
      body: JSON.stringify(body),
    })
      .then(async (res) => {
        if (!res.ok) {
          const errorData = await res.json();
          const tokenError = errorData.error || "unknown_error";
          const tokenErrorDesc =
            errorData.error_description || "Token exchange failed";

          const error = new Error(tokenErrorDesc);
          (error as any).code = tokenError;
          throw error;
        }
        return res.json();
      })
      .then((data) => {
        setStatus("Success! Redirecting...");
        setTimeout(() => navigate("/"), 500);
      })
      .catch((err) => {
        console.error("Token exchange error:", err);
        setError(err.message);
        setStatus("Token exchange failed");

        let shouldRetryAuth = false;
        if (err.code === "invalid_grant") {
          shouldRetryAuth = true;
        } else if (
          err.code === "invalid_client" ||
          err.code === "unauthorized_client"
        ) {
          shouldRetryAuth = false;
        }

        const path = shouldRetryAuth ? "/oauth/authorize" : "/login";
        setRedirectPath(path);
        setCountdown(5);
      });
  }, [navigate]);

  useEffect(() => {
    if (countdown === null) return;

    if (countdown <= 0) {
      navigate(redirectPath);
      return;
    }

    const timer = setInterval(() => {
      setCountdown((prev) => (prev !== null && prev > 0 ? prev - 1 : 0));
    }, 1000);

    return () => clearInterval(timer);
  }, [countdown, navigate, redirectPath]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="p-8 text-center bg-white rounded-lg shadow-md max-w-md w-full">
        <h1 className="text-xl font-mono mb-4">{status}</h1>

        {error ? (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded">
            <p className="text-red-800 text-sm mb-2">{error}</p>
            {countdown !== null && (
              <div className="flex items-center justify-center gap-2">
                <div className="relative">
                  <div className="w-8 h-8 rounded-full border-2 border-red-300 flex items-center justify-center">
                    <span className="text-red-600 font-mono text-sm font-semibold">
                      {countdown}
                    </span>
                  </div>
                </div>
                <p className="text-red-600 text-xs">
                  Redirecting in {countdown} second{countdown !== 1 ? "s" : ""}
                  ...
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="animate-spin text-4xl">🌀</div>
        )}

        {error && (
          <div className="flex gap-2 justify-center">
            <button
              onClick={() => navigate("/oauth/authorize")}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => navigate("/login")}
              className="mt-4 px-4 py-2 bg-gray-800 text-white rounded hover:bg-gray-700 transition-colors"
            >
              Back to Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
