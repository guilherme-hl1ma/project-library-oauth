import { useEffect, useState } from "react";
import { useNavigate } from "react-router";

export default function OAuthCallback() {
  const navigate = useNavigate();
  const [status, setStatus] = useState("Initializing...");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

    if (code) {
      setStatus("Exchanging code for token...");

      fetch("http://localhost:8000/token", {
        method: "POST",
        body: JSON.stringify({ code }),
      })
        .then((res) => res.json())
        .then((data) => {
          localStorage.setItem("token", data.access_token);
          navigate("/dashboard");
        })
        .catch(() => setStatus("Error during exchange"));
    }
  }, [navigate]);

  return (
    <div className="p-8 text-center">
      <h1 className="text-xl font-mono">{status}</h1>
      <div className="animate-spin mt-4">🌀</div>
    </div>
  );
}
