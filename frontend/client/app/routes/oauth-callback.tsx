import { useEffect } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";

export default function OAuthCallback() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const code = searchParams.get("code");
    const state = searchParams.get("state");

    if (code) {
      console.log("Código de autorização recebido:", code);

      // Validação opcional do state (se você salvou no localStorage antes de ir)
      // if (state !== localStorage.getItem('auth_state')) { ... erro ... }

      // Agora o FRONT do CLIENT envia o código para o BACK do CLIENT
      // (Não confunda com o Auth Server!)
      exchangeCodeForToken(code);
    }
  }, [searchParams]);

  const exchangeCodeForToken = async (code) => {
    try {
      // O seu back-end (Client) vai fazer a chamada "escondida" para o Auth Server
      // const response = await axios.post(
      //   "http://localhost:8000/api/token-exchange",
      //   {
      //     code: code,
      //   },
      // );

      // Salva o JWT final que o SEU sistema gerou
      localStorage.setItem("access_token", response.data.access_token);

      // Leva o usuário para a área logada
      navigate("/dashboard");
    } catch (error) {
      console.error("Erro na troca do token:", error);
      navigate("/login?error=failed_exchange");
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <h2 className="text-xl font-semibold">Finalizando autenticação...</h2>
        <p className="text-gray-500">Aguarde um instante.</p>
      </div>
    </div>
  );
}
