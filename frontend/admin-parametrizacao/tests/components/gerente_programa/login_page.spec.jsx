import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "../../../src/pages/Login";
import { ROUTES } from "../../../src/utils/routes";
import { registerCase } from "../../support/caseLog";

const { navigateMock, loginMock, setTokenMock, useLoginMock } = vi.hoisted(
  () => ({
    navigateMock: vi.fn(),
    loginMock: vi.fn(),
    setTokenMock: vi.fn(),
    useLoginMock: vi.fn(),
  }),
);

vi.mock("react-router", async () => {
  const actual = await vi.importActual("react-router");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/hooks/useLogin", () => ({
  default: () => useLoginMock(),
}));

vi.mock("../../../src/utils/authStorage", () => ({
  default: {
    setToken: setTokenMock,
  },
}));

describe("Gerente de Programa - Página de Login", () => {
  beforeEach(() => {
    navigateMock.mockReset();
    loginMock.mockReset();
    setTokenMock.mockReset();
    useLoginMock.mockReset();
    useLoginMock.mockReturnValue({
      login: loginMock,
      isPending: false,
    });
  });

  it("salva o token e navega para a home quando o login é bem-sucedido", async () => {
    loginMock.mockResolvedValue({ access_token: "admin-token" });
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        email: "admin@example.com",
        password: "senha-segura",
      },
      expected: {
        tokenSaved: "admin-token",
        navigateTo: ROUTES.HOME,
      },
    });

    render(<Login />);

    await user.type(screen.getByLabelText(/email/i), "admin@example.com");
    await user.type(screen.getByLabelText(/senha/i), "senha-segura");
    await user.click(screen.getByRole("button", { name: /acessar painel/i }));

    await waitFor(() => {
      expect(setTokenMock).toHaveBeenCalledWith("admin-token");
      expect(navigateMock).toHaveBeenCalledWith(ROUTES.HOME);
    });

    caseLog.output = {
      setTokenCalls: setTokenMock.mock.calls,
      navigateCalls: navigateMock.mock.calls,
    };
  });

  it("mostra erro local quando o hook retorna usuário nulo", async () => {
    loginMock.mockResolvedValue(null);
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        loginResult: null,
      },
      expected: {
        error: "Erro ao fazer login",
        navigateCalls: 0,
      },
    });

    render(<Login />);

    await user.type(screen.getByLabelText(/email/i), "admin@example.com");
    await user.type(screen.getByLabelText(/senha/i), "senha-segura");
    await user.click(screen.getByRole("button", { name: /acessar painel/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Erro ao fazer login",
    );
    expect(navigateMock).not.toHaveBeenCalled();

    caseLog.output = {
      renderedError: screen.getByRole("alert").textContent,
      navigateCalls: navigateMock.mock.calls.length,
    };
  });

  it("mostra erro de conexão quando o hook lança exceção", async () => {
    loginMock.mockRejectedValue(new Error("network down"));
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        loginThrows: "network down",
      },
      expected: {
        error: "Erro de conexão tente novamente",
      },
    });

    render(<Login />);

    await user.type(screen.getByLabelText(/email/i), "admin@example.com");
    await user.type(screen.getByLabelText(/senha/i), "senha-segura");
    await user.click(screen.getByRole("button", { name: /acessar painel/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Erro de conexão tente novamente",
    );

    caseLog.output = {
      renderedError: screen.getByRole("alert").textContent,
    };
  });
});
