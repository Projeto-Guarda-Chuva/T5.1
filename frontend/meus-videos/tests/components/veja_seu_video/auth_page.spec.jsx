import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import AuthPage from "../../../src/pages/Login";
import { ROUTES } from "../../../src/utils/routes";
import { registerCase } from "../../support/caseLog";

const navigateMock = vi.fn();
const loginMock = vi.fn();
const registerMock = vi.fn();
const loginWithGoogleMock = vi.fn();
const aceitarTermoMock = vi.fn();
const jwtDecodeMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/services/authService", () => ({
  default: {
    login: (...args) => loginMock(...args),
    register: (...args) => registerMock(...args),
    loginWithGoogle: (...args) => loginWithGoogleMock(...args),
  },
}));

vi.mock("../../../src/services/participantesService", () => ({
  default: {
    aceitarTermo: (...args) => aceitarTermoMock(...args),
  },
}));

vi.mock("jwt-decode", () => ({
  jwtDecode: (...args) => jwtDecodeMock(...args),
}));

vi.mock("@react-oauth/google", () => ({
  GoogleOAuthProvider: ({ children }) => (
    <div data-testid="google-provider">{children}</div>
  ),
  GoogleLogin: ({ onSuccess, onError }) => (
    <div>
      <button type="button" onClick={() => onSuccess?.({ credential: "google-token" })}>
        Google sucesso
      </button>
      <button type="button" onClick={() => onSuccess?.({})}>
        Google sem credencial
      </button>
      <button type="button" onClick={() => onError?.()}>
        Google erro
      </button>
    </div>
  ),
}));

function renderAuthPage() {
  return render(
    <MemoryRouter>
      <AuthPage />
    </MemoryRouter>,
  );
}

describe("Aplicação Veja seu Vídeo - Autenticação", () => {
  beforeEach(() => {
    navigateMock.mockReset();
    loginMock.mockReset();
    registerMock.mockReset();
    loginWithGoogleMock.mockReset();
    aceitarTermoMock.mockReset();
    jwtDecodeMock.mockReset();
    jwtDecodeMock.mockReturnValue({
      name: "Usuário Google",
      email: "google@example.com",
    });
  });

  it("valida campos obrigatórios no login", async () => {
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        activeTab: "login",
        formData: {
          email: "",
          password: "",
        },
      },
      expected: {
        errors: ["O e-mail é obrigatório.", "A senha é obrigatória."],
      },
    });

    renderAuthPage();
    await user.click(screen.getByRole("button", { name: /^entrar$/i }));

    expect(screen.getByText("O e-mail é obrigatório.")).toBeInTheDocument();
    expect(screen.getByText("A senha é obrigatória.")).toBeInTheDocument();

    caseLog.output = {
      renderedErrors: [
        screen.getByText("O e-mail é obrigatório.").textContent,
        screen.getByText("A senha é obrigatória.").textContent,
      ],
    };
  });

  it("realiza login, salva token e navega para a home", async () => {
    loginMock.mockResolvedValue({ access_token: "jwt-token" });
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        email: "participante@example.com",
        password: "segredo",
      },
      expected: {
        accessToken: "jwt-token",
        navigateTo: ROUTES.HOME,
      },
    });

    renderAuthPage();

    await user.type(
      screen.getByPlaceholderText("seu@email.com"),
      "participante@example.com",
    );
    await user.type(screen.getByPlaceholderText("*******"), "segredo");
    await user.click(screen.getByRole("button", { name: /^entrar$/i }));

    await waitFor(() => {
      expect(localStorage.getItem("access_token")).toBe("jwt-token");
      expect(navigateMock).toHaveBeenCalledWith(ROUTES.HOME);
    });

    caseLog.output = {
      accessToken: localStorage.getItem("access_token"),
      loggedUser: JSON.parse(localStorage.getItem("logged_user") || "{}"),
      navigateCalls: navigateMock.mock.calls,
    };
  });

  it("mostra mensagem da API quando o login falha", async () => {
    loginMock.mockRejectedValue({
      response: {
        data: {
          detail: "Credenciais inválidas",
        },
      },
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        email: "participante@example.com",
        password: "segredo",
        apiDetail: "Credenciais inválidas",
      },
      expected: {
        error: "Credenciais inválidas",
      },
    });

    renderAuthPage();

    await user.type(
      screen.getByPlaceholderText("seu@email.com"),
      "participante@example.com",
    );
    await user.type(screen.getByPlaceholderText("*******"), "segredo");
    await user.click(screen.getByRole("button", { name: /^entrar$/i }));

    expect(await screen.findByText("Credenciais inválidas")).toBeInTheDocument();

    caseLog.output = {
      renderedError: screen.getByText("Credenciais inválidas").textContent,
    };
  });

  it("valida nome, email, senha e consentimento no cadastro", async () => {
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        activeTab: "cadastro",
        formData: {
          nome: "",
          email: "",
          password: "",
          consentimento: false,
        },
      },
      expected: {
        errors: [
          "O nome é obrigatório.",
          "O e-mail é obrigatório.",
          "A senha é obrigatória.",
          "Você deve aceitar o termo de consentimento.",
        ],
      },
    });

    renderAuthPage();
    await user.click(screen.getByRole("button", { name: /cadastro/i }));
    await user.click(screen.getByRole("button", { name: /^cadastrar$/i }));

    expect(screen.getByText("O nome é obrigatório.")).toBeInTheDocument();
    expect(screen.getByText("O e-mail é obrigatório.")).toBeInTheDocument();
    expect(screen.getByText("A senha é obrigatória.")).toBeInTheDocument();
    expect(
      screen.getByText("Você deve aceitar o termo de consentimento."),
    ).toBeInTheDocument();

    caseLog.output = {
      renderedErrors: [
        "O nome é obrigatório.",
        "O e-mail é obrigatório.",
        "A senha é obrigatória.",
        "Você deve aceitar o termo de consentimento.",
      ],
    };
  });

  it("encadeia cadastro, login e aceite de termo quando o cadastro é bem-sucedido", async () => {
    registerMock.mockResolvedValue({
      participant_id: "part-001",
      email: "novo@example.com",
      nome: "Novo Usuário",
      message: "ok",
    });
    loginMock.mockResolvedValue({ access_token: "novo-token" });
    aceitarTermoMock.mockResolvedValue({ ok: true });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        nome: "Novo Usuário",
        email: "novo@example.com",
        password: "senha-forte",
        consentimento: true,
      },
      expected: {
        accessToken: "novo-token",
        participantId: "part-001",
        navigateTo: ROUTES.STATUS_GRAVACAO,
      },
    });

    renderAuthPage();
    await user.click(screen.getByRole("button", { name: /cadastro/i }));

    await user.type(screen.getByPlaceholderText("João"), "Novo Usuário");
    await user.type(screen.getByPlaceholderText("seu@email.com"), "novo@example.com");
    await user.type(screen.getByPlaceholderText("*******"), "senha-forte");
    await user.click(screen.getByRole("checkbox"));
    await user.click(screen.getByRole("button", { name: /^cadastrar$/i }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalled();
      expect(loginMock).toHaveBeenCalledWith({
        email: "novo@example.com",
        password: "senha-forte",
      });
      expect(aceitarTermoMock).toHaveBeenCalledWith("part-001", {
        aceitou: true,
        versao_termo: "v1.0",
      });
      expect(navigateMock).toHaveBeenCalledWith(ROUTES.STATUS_GRAVACAO);
    });

    caseLog.output = {
      accessToken: localStorage.getItem("access_token"),
      loggedUser: JSON.parse(localStorage.getItem("logged_user") || "{}"),
      navigateCalls: navigateMock.mock.calls,
    };
  });

  it("mostra erro quando o Google retorna sucesso sem credential", async () => {
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "google-client");
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        credential: null,
      },
      expected: {
        error: "Login com Google falhou. Tente novamente.",
      },
    });

    renderAuthPage();
    await user.click(screen.getByRole("button", { name: /google sem credencial/i }));

    expect(
      screen.getByText("Login com Google falhou. Tente novamente."),
    ).toBeInTheDocument();

    caseLog.output = {
      renderedError: screen.getByText(
        "Login com Google falhou. Tente novamente.",
      ).textContent,
    };
  });

  it("realiza login com Google e navega para status quando o usuário é novo", async () => {
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "google-client");
    loginWithGoogleMock.mockResolvedValue({
      access_token: "google-jwt",
      token_type: "bearer",
      participant_id: "part-google",
      email: "google@example.com",
      nome: "Usuário Google",
      is_new_user: true,
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        credential: "google-token",
      },
      expected: {
        accessToken: "google-jwt",
        navigateTo: ROUTES.STATUS_GRAVACAO,
      },
    });

    renderAuthPage();
    await user.click(screen.getByRole("button", { name: /google sucesso/i }));

    await waitFor(() => {
      expect(loginWithGoogleMock).toHaveBeenCalledWith({
        credential: "google-token",
      });
      expect(localStorage.getItem("access_token")).toBe("google-jwt");
      expect(navigateMock).toHaveBeenCalledWith(ROUTES.STATUS_GRAVACAO);
    });

    caseLog.output = {
      accessToken: localStorage.getItem("access_token"),
      loggedUser: JSON.parse(localStorage.getItem("logged_user") || "{}"),
      navigateCalls: navigateMock.mock.calls,
    };
  });

});
