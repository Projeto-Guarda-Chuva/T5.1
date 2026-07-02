import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Parameters from "../../../src/pages/Parameters";
import { registerCase } from "../../support/caseLog";

const useConfigurationsMock = vi.fn();
const useDetailsConfigurationsMock = vi.fn();
const useCreateConfigurationMock = vi.fn();
const useActivateConfigurationMock = vi.fn();
const invalidateQueriesMock = vi.fn();

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({
    invalidateQueries: invalidateQueriesMock,
  }),
}));

vi.mock("../../../src/hooks/useConfigurations", () => ({
  CONFIGURATIONS_KEY: "configurations",
  default: () => useConfigurationsMock(),
}));

vi.mock("../../../src/hooks/useDetailsConfigurations", () => ({
  default: (...args) => useDetailsConfigurationsMock(...args),
}));

vi.mock("../../../src/hooks/useCreateConfiguration", () => ({
  default: (options) => useCreateConfigurationMock(options),
}));

vi.mock("../../../src/hooks/useActivateConfiguration", () => ({
  default: (options) => useActivateConfigurationMock(options),
}));

vi.mock("../../../src/pages/Parameters/CreateConfigurationModal", () => ({
  default: ({ isOpen, onClose }) =>
    isOpen ? (
      <div data-testid="create-configuration-modal">
        <button type="button" onClick={onClose}>
          Fechar modal de criação
        </button>
      </div>
    ) : null,
}));

vi.mock("../../../src/pages/Parameters/ViewConfigurationModal", () => ({
  default: ({ configDetail, onClose }) => (
    <div data-testid="view-configuration-modal">
      <span>{configDetail?.name ?? "Sem detalhe"}</span>
      <button type="button" onClick={onClose}>
        Fechar detalhes
      </button>
    </div>
  ),
}));

const configurationsPayload = {
  items: [
    {
      id: "cfg-active",
      name: "Ativa",
      description: "Configuração ativa",
      is_active: true,
      created_at: "2026-06-30T10:00:00Z",
      updated_at: "2026-06-30T12:00:00Z",
    },
    {
      id: "cfg-inactive",
      name: "Inativa",
      description: "Configuração pronta para aplicar",
      is_active: false,
      created_at: "2026-06-29T10:00:00Z",
      updated_at: "2026-06-29T12:00:00Z",
    },
  ],
  total: 2,
  message: "ok",
};

describe("Gerente de Programa - Página de Parâmetros", () => {
  beforeEach(() => {
    invalidateQueriesMock.mockReset();
    useConfigurationsMock.mockReset();
    useDetailsConfigurationsMock.mockReset();
    useCreateConfigurationMock.mockReset();
    useActivateConfigurationMock.mockReset();

    useConfigurationsMock.mockReturnValue({
      configurations: configurationsPayload,
      isLoading: false,
      error: null,
    });

    useDetailsConfigurationsMock.mockReturnValue({
      configurationDetail: {
        id: "cfg-inactive",
        name: "Inativa",
      },
      isLoading: false,
      error: null,
    });

    useCreateConfigurationMock.mockReturnValue({
      createConfiguration: vi.fn(),
      isPending: false,
    });

    useActivateConfigurationMock.mockReturnValue({
      activateConfiguration: vi.fn(),
      isPending: false,
    });
  });

  it("lista configurações, abre modal de criação e mostra detalhes da configuração selecionada", async () => {
    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        totalConfigurations: configurationsPayload.total,
      },
      expected: {
        activeBadge: "Ativa",
        inactiveBadge: "Inativa",
        createModalVisible: true,
        detailsVisible: "Inativa",
      },
    });

    render(<Parameters />);

    expect(screen.getByText("Configuração ativa")).toBeInTheDocument();
    expect(
      screen.getByText("Configuração pronta para aplicar"),
    ).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /ver detalhes/i })).toHaveLength(
      2,
    );

    await user.click(
      screen.getByRole("button", { name: /nova configuração/i }),
    );
    expect(
      screen.getByTestId("create-configuration-modal"),
    ).toBeInTheDocument();

    await user.click(screen.getAllByRole("button", { name: /ver detalhes/i })[1]);
    expect(
      screen.getByTestId("view-configuration-modal"),
    ).toHaveTextContent("Inativa");

    caseLog.output = {
      createModalVisible: true,
      detailsText:
        screen.getByTestId("view-configuration-modal").textContent,
    };
  });

  it("mostra o loading modal enquanto a tela aguarda dados", () => {
    useConfigurationsMock.mockReturnValue({
      configurations: { items: [], total: 0, message: "ok" },
      isLoading: true,
      error: null,
    });

    const caseLog = registerCase({
      input: {
        isLoading: true,
        isPending: false,
      },
      expected: {
        loadingVisible: true,
      },
    });

    render(<Parameters />);

    expect(screen.getByText("Carregando...")).toBeInTheDocument();

    caseLog.output = {
      loadingText: screen.getByText("Carregando...").textContent,
    };
  });

  it("deve classificar erro 4xx de ativação como erro interno da aplicação", async () => {
    const user = userEvent.setup();
    useActivateConfigurationMock.mockImplementation((options) => ({
      activateConfiguration: vi.fn(async () => {
        await options?.onError?.({ status: 422 });
      }),
      isPending: false,
    }));

    const caseLog = registerCase({
      input: {
        activateErrorStatus: 422,
      },
      expected: {
        errorMessage: "Erro no servidor interno da aplicação",
      },
      notes: [
        "Teste propositalmente alinhado ao comportamento esperado do requisito.",
      ],
    });

    render(<Parameters />);

    await user.click(screen.getByRole("button", { name: /aplicar/i }));

    const renderedMessage = await screen.findByText(
      "Erro no servidor interno da aplicação",
    );
    caseLog.output = {
      renderedMessage: renderedMessage.textContent,
    };

    expect(
      screen.getByText("Erro no servidor interno da aplicação"),
    ).toBeInTheDocument();
  });
});
