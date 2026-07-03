import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import Form from "../../../src/components/Form";
import { registerCase } from "../../support/caseLog";

describe("Aplicação Veja seu Vídeo - Formulário de Registro de Participação", () => {
  it("não renderiza nada quando o modal está fechado", () => {
    const caseLog = registerCase({
      input: {
        isOpen: false,
      },
      expected: {
        root: null,
      },
    });

    const { container } = render(
      <Form isOpen={false} onClose={vi.fn()} onSubmit={vi.fn()} />,
    );

    expect(container.firstChild).toBeNull();

    caseLog.output = {
      firstChild: container.firstChild,
    };
  });

  it("mostra erro quando o usuário tenta confirmar sem horário", () => {
    const caseLog = registerCase({
      input: {
        time: "",
      },
      expected: {
        error: "Por favor, selecione uma hora.",
      },
    });

    render(<Form isOpen onClose={vi.fn()} onSubmit={vi.fn()} />);
    fireEvent.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(screen.getByText("Por favor, selecione uma hora.")).toBeInTheDocument();

    caseLog.output = {
      renderedError: screen.getByText("Por favor, selecione uma hora.").textContent,
    };
  });

  it("bloqueia horário no futuro", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-01T12:00:00"));

    const caseLog = registerCase({
      input: {
        currentTime: "2026-07-01T12:00:00",
        selectedTime: "12:30",
      },
      expected: {
        error: "O horário da participação não pode estar no futuro.",
      },
    });

    const { container } = render(
      <Form isOpen onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    const timeInput = container.querySelector('input[type="time"]');

    fireEvent.change(timeInput, { target: { value: "12:30" } });
    fireEvent.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(
      screen.getByText("O horário da participação não pode estar no futuro."),
    ).toBeInTheDocument();

    caseLog.output = {
      renderedError: screen.getByText(
        "O horário da participação não pode estar no futuro.",
      ).textContent,
    };
  });

  it("bloqueia participação com mais de uma hora", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-01T12:00:00"));

    const caseLog = registerCase({
      input: {
        currentTime: "2026-07-01T12:00:00",
        selectedTime: "10:30",
      },
      expected: {
        error: "A participação deve ter ocorrido no máximo há 1 hora.",
      },
    });

    const { container } = render(
      <Form isOpen onClose={vi.fn()} onSubmit={vi.fn()} />,
    );
    const timeInput = container.querySelector('input[type="time"]');

    fireEvent.change(timeInput, { target: { value: "10:30" } });
    fireEvent.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(
      screen.getByText("A participação deve ter ocorrido no máximo há 1 hora."),
    ).toBeInTheDocument();

    caseLog.output = {
      renderedError: screen.getByText(
        "A participação deve ter ocorrido no máximo há 1 hora.",
      ).textContent,
    };
  });

  it("aceita horário recente válido e limpa o campo após envio", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-01T12:00:00"));

    const onSubmit = vi.fn();
    const caseLog = registerCase({
      input: {
        currentTime: "2026-07-01T12:00:00",
        selectedTime: "11:30",
      },
      expected: {
        onSubmit: "11:30",
      },
    });

    const { container } = render(
      <Form isOpen onClose={vi.fn()} onSubmit={onSubmit} />,
    );
    const timeInput = container.querySelector('input[type="time"]');

    fireEvent.change(timeInput, { target: { value: "11:30" } });
    fireEvent.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(onSubmit).toHaveBeenCalledWith("11:30");
    expect(timeInput.value).toBe("");

    caseLog.output = {
      submitCalls: onSubmit.mock.calls,
      finalTimeValue: timeInput.value,
    };
  });

  it("aceita horário da noite anterior quando a diferença cruza a virada do dia", () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-07-01T00:15:00"));

    const onSubmit = vi.fn();
    const caseLog = registerCase({
      input: {
        currentTime: "2026-07-01T00:15:00",
        selectedTime: "23:30",
      },
      expected: {
        onSubmit: "23:30",
      },
    });

    const { container } = render(
      <Form isOpen onClose={vi.fn()} onSubmit={onSubmit} />,
    );
    const timeInput = container.querySelector('input[type="time"]');

    fireEvent.change(timeInput, { target: { value: "23:30" } });
    fireEvent.click(screen.getByRole("button", { name: /confirmar/i }));

    expect(onSubmit).toHaveBeenCalledWith("23:30");

    caseLog.output = {
      submitCalls: onSubmit.mock.calls,
    };
  });
});
