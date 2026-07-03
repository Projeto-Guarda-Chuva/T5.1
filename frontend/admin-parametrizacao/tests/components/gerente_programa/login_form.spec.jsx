import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import LoginForm from "../../../src/components/LoginForm";
import { registerCase } from "../../support/caseLog";

describe("Gerente de Programa - LoginForm", () => {
  it("envia as credenciais digitadas", async () => {
    const onSubmit = vi.fn();
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        email: "admin@example.com",
        password: "senha-segura",
        loading: false,
      },
      expected: {
        onSubmit: {
          email: "admin@example.com",
          password: "senha-segura",
        },
      },
    });

    render(<LoginForm onSubmit={onSubmit} loading={false} error={undefined} />);

    await user.type(screen.getByLabelText(/email/i), "admin@example.com");
    await user.type(screen.getByLabelText(/senha/i), "senha-segura");
    await user.click(screen.getByRole("button", { name: /acessar painel/i }));

    expect(onSubmit).toHaveBeenCalledWith({
      email: "admin@example.com",
      password: "senha-segura",
    });

    caseLog.output = {
      submitCalls: onSubmit.mock.calls,
    };
  });

  it("exibe a mensagem de erro recebida e marca os campos como inválidos", () => {
    const caseLog = registerCase({
      input: {
        error: "Credenciais inválidas",
      },
      expected: {
        alert: "Credenciais inválidas",
        invalidFields: ["Email", "Senha"],
      },
    });

    render(
      <LoginForm
        onSubmit={vi.fn()}
        loading={false}
        error="Credenciais inválidas"
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Credenciais inválidas");

    const emailField = screen.getByLabelText(/email/i);
    const passwordField = screen.getByLabelText(/senha/i);

    expect(emailField).toHaveClass("is-invalid");
    expect(passwordField).toHaveClass("is-invalid");

    caseLog.output = {
      emailClass: emailField.className,
      passwordClass: passwordField.className,
    };
  });

  it("desabilita os controles enquanto o login está carregando", () => {
    const caseLog = registerCase({
      input: {
        loading: true,
      },
      expected: {
        buttonLabel: "Acessando...",
        fieldsDisabled: true,
      },
    });

    render(<LoginForm onSubmit={vi.fn()} loading error={undefined} />);

    const emailField = screen.getByLabelText(/email/i);
    const passwordField = screen.getByLabelText(/senha/i);
    const submitButton = screen.getByRole("button", { name: /acessando/i });

    expect(emailField).toBeDisabled();
    expect(passwordField).toBeDisabled();
    expect(submitButton).toBeDisabled();

    caseLog.output = {
      buttonText: submitButton.textContent,
      emailDisabled: emailField.hasAttribute("disabled"),
      passwordDisabled: passwordField.hasAttribute("disabled"),
    };
  });
});
