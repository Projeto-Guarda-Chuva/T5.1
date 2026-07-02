import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import CreateConfigurationModal from "../../../src/pages/Parameters/CreateConfigurationModal";
import { registerCase } from "../../support/caseLog";

describe("Gerente de Programa - Modal de Nova Configuração", () => {
  it("impede o salvamento quando o nome obrigatório não foi informado", () => {
    const caseLog = registerCase({
      input: {
        name: "",
        description: "",
      },
      expected: {
        saveDisabled: true,
      },
    });

    render(
      <CreateConfigurationModal
        isOpen
        onClose={vi.fn()}
        onSubmit={vi.fn().mockResolvedValue(undefined)}
      />,
    );

    const saveButton = screen.getByRole("button", { name: /salvar configuração/i });
    expect(saveButton).toBeDisabled();

    caseLog.output = {
      saveDisabled: saveButton.hasAttribute("disabled"),
    };
  });

  it("envia os dados preenchidos da nova configuração para salvamento", async () => {
    const user = userEvent.setup();
    const onCloseMock = vi.fn();
    const onSubmitMock = vi.fn().mockResolvedValue(undefined);
    const caseLog = registerCase({
      input: {
        name: "Modo Exposição Padrão",
        description: "Configuração criada pela interface web",
        movement_speed: 2.5,
        movement_duration_seconds: 45,
        video_capture_enabled: true,
      },
      expected: {
        submittedName: "Modo Exposição Padrão",
        submittedDuration: 45,
        closeCalled: true,
      },
    });

    render(
      <CreateConfigurationModal
        isOpen
        onClose={onCloseMock}
        onSubmit={onSubmitMock}
      />,
    );

    const nameInput = screen.getByPlaceholderText("Ex: Modo Exposição Padrão");
    const descriptionInput = screen.getByPlaceholderText(
      "Descreva o propósito desta configuração...",
    );
    const [speedInput, durationInput] = screen.getAllByRole("spinbutton");
    const switches = screen.getAllByRole("switch");

    await user.type(nameInput, "Modo Exposição Padrão");
    await user.type(
      descriptionInput,
      "Configuração criada pela interface web",
    );
    await user.clear(speedInput);
    await user.type(speedInput, "2.5");
    await user.clear(durationInput);
    await user.type(durationInput, "45");
    await user.click(switches[0]);
    await user.click(screen.getByRole("button", { name: /salvar configuração/i }));

    expect(onSubmitMock).toHaveBeenCalledWith({
      name: "Modo Exposição Padrão",
      description: "Configuração criada pela interface web",
      is_active: false,
      parameters: {
        movement_speed: 2.5,
        movement_duration_seconds: 45,
        video_capture_enabled: true,
        audio_capture_enabled: false,
      },
    });
    expect(onCloseMock).toHaveBeenCalled();

    caseLog.output = {
      submitPayload: onSubmitMock.mock.calls[0]?.[0],
      closeCalls: onCloseMock.mock.calls.length,
    };
  });
});
