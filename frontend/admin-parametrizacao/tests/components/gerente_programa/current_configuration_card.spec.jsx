import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import CurrentConfigurationCard from "../../../src/pages/Home/CurrentConfigurationCard";
import { registerCase } from "../../support/caseLog";

const configuration = {
  id: "cfg-001",
  name: "Configuração Oceano",
  description: "Parâmetros para operação padrão",
  is_active: true,
  created_at: "2026-06-30T10:00:00Z",
  updated_at: "2026-06-30T12:00:00Z",
  parameters: {
    movement_speed: 4.2,
    movement_duration_seconds: 18,
    video_capture_enabled: true,
    audio_capture_enabled: false,
  },
};

describe("Gerente de Programa - Card de Configuração Ativa", () => {
  it("mostra estado vazio quando não existe configuração ativa", () => {
    const caseLog = registerCase({
      input: {
        currentConfiguration: null,
      },
      expected: {
        message: "Nenhuma configuração ativa",
      },
    });

    render(<CurrentConfigurationCard currentConfiguration={undefined} />);

    expect(screen.getByText("Nenhuma configuração ativa")).toBeInTheDocument();

    caseLog.output = {
      renderedMessage: "Nenhuma configuração ativa",
    };
  });

  it("mostra o resumo dos parâmetros quando existe configuração ativa", () => {
    const caseLog = registerCase({
      input: configuration,
      expected: {
        name: configuration.name,
        speed: configuration.parameters.movement_speed,
        duration: configuration.parameters.movement_duration_seconds,
      },
    });

    render(<CurrentConfigurationCard currentConfiguration={configuration} />);

    expect(screen.getByText(configuration.name)).toBeInTheDocument();
    expect(screen.getByText(configuration.description)).toBeInTheDocument();
    expect(
      screen.getByText(String(configuration.parameters.movement_speed)),
    ).toBeInTheDocument();
    expect(
      screen.getByText(`${configuration.parameters.movement_duration_seconds}s`),
    ).toBeInTheDocument();

    caseLog.output = {
      renderedName: configuration.name,
      renderedSpeed: String(configuration.parameters.movement_speed),
      renderedDuration: `${configuration.parameters.movement_duration_seconds}s`,
    };
  });

  it("mantém as informações básicas quando a configuração ativa não possui parâmetros detalhados", () => {
    const parameterlessConfiguration = {
      ...configuration,
      id: "cfg-002",
      name: "Configuração sem parâmetros",
      parameters: undefined,
    };
    const caseLog = registerCase({
      input: {
        currentConfiguration: {
          id: parameterlessConfiguration.id,
          name: parameterlessConfiguration.name,
          hasParameters: false,
        },
      },
      expected: {
        name: parameterlessConfiguration.name,
        detailsHidden: true,
      },
    });

    render(
      <CurrentConfigurationCard currentConfiguration={parameterlessConfiguration} />,
    );

    expect(screen.getByText(parameterlessConfiguration.name)).toBeInTheDocument();
    expect(screen.queryByText("Velocidade")).not.toBeInTheDocument();
    expect(screen.queryByText("Duração")).not.toBeInTheDocument();

    caseLog.output = {
      renderedName: parameterlessConfiguration.name,
      hasSpeedField: Boolean(screen.queryByText("Velocidade")),
      hasDurationField: Boolean(screen.queryByText("Duração")),
    };
  });
});
