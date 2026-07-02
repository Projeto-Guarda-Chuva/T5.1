import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import StatusGravacao from "../../../src/pages/StatusGravacao";
import { ROUTES } from "../../../src/utils/routes";
import { registerCase } from "../../support/caseLog";

const navigateMock = vi.fn();
const marcarQueJaParticipouMock = vi.fn();
const marcarQueVaiParticiparMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/services/participantesService", () => ({
  default: {
    marcarQueJaParticipou: (...args) => marcarQueJaParticipouMock(...args),
    marcarQueVaiParticipar: (...args) => marcarQueVaiParticiparMock(...args),
  },
}));

function renderStatusPage() {
  return render(
    <MemoryRouter>
      <StatusGravacao />
    </MemoryRouter>,
  );
}

describe("Aplicação Veja seu Vídeo - Status de Gravação", () => {
  beforeEach(() => {
    navigateMock.mockReset();
    marcarQueJaParticipouMock.mockReset();
    marcarQueVaiParticiparMock.mockReset();
  });

  it("impede envio sem seleção de status", () => {
    const caseLog = registerCase({
      input: {
        selectedStatus: null,
      },
      expected: {
        alert: "Por favor, selecione uma opção!",
      },
    });

    const { container } = renderStatusPage();
    const form = container.querySelector("form");

    fireEvent.submit(form);

    expect(globalThis.alert).toHaveBeenCalledWith(
      "Por favor, selecione uma opção!",
    );

    caseLog.output = {
      alertCalls: globalThis.alert.mock.calls,
    };
  });

  it("registra o caminho de quem já participou, atualiza o localStorage e navega para a home", async () => {
    localStorage.setItem(
      "logged_user",
      JSON.stringify({ email: "participante@example.com" }),
    );
    marcarQueJaParticipouMock.mockResolvedValue({
      participant_id: "part-001",
      participant_email: "participante@example.com",
      event_type: "already_participated",
      recorded_at: "2026-07-01T12:15:00Z",
      associated_video_ids: ["video-001"],
      associated_videos_count: 1,
      message: "Status atualizado com sucesso.",
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        selectedStatus: "ja_participei",
      },
      expected: {
        service: "marcarQueJaParticipou",
        navigateTo: ROUTES.HOME,
      },
    });

    renderStatusPage();

    await user.click(
      screen.getByRole("button", { name: /já participei da gravação/i }),
    );
    await user.click(
      screen.getByRole("button", { name: /confirmar e acessar/i }),
    );

    await waitFor(() => {
      expect(marcarQueJaParticipouMock).toHaveBeenCalledTimes(1);
      expect(navigateMock).toHaveBeenCalledWith(ROUTES.HOME);
    });

    caseLog.output = {
      loggedUser: JSON.parse(localStorage.getItem("logged_user") || "{}"),
      navigateCalls: navigateMock.mock.calls,
      alertCalls: globalThis.alert.mock.calls,
    };
  });

  it("registra o caminho de quem ainda vai participar", async () => {
    marcarQueVaiParticiparMock.mockResolvedValue({
      participant_id: "part-002",
      participant_email: "futuro@example.com",
      event_type: "will_participate",
      recorded_at: "2026-07-01T13:00:00Z",
      associated_video_ids: [],
      associated_videos_count: 0,
      message: "Status salvo.",
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        selectedStatus: "ainda_participarei",
      },
      expected: {
        service: "marcarQueVaiParticipar",
      },
    });

    renderStatusPage();

    await user.click(
      screen.getByRole("button", {
        name: /ainda vou participar da próxima gravação/i,
      }),
    );
    await user.click(
      screen.getByRole("button", { name: /confirmar e acessar/i }),
    );

    await waitFor(() => {
      expect(marcarQueVaiParticiparMock).toHaveBeenCalledTimes(1);
    });

    caseLog.output = {
      jaParticipouCalls: marcarQueJaParticipouMock.mock.calls.length,
      aindaVaiCalls: marcarQueVaiParticiparMock.mock.calls.length,
    };
  });

  it("mostra detalhe de erro da API quando a atualização falha", async () => {
    marcarQueJaParticipouMock.mockRejectedValue({
      response: {
        data: {
          detail: "Participante não encontrado",
        },
      },
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        selectedStatus: "ja_participei",
        apiDetail: "Participante não encontrado",
      },
      expected: {
        alert: "Participante não encontrado",
      },
    });

    renderStatusPage();

    await user.click(
      screen.getByRole("button", { name: /já participei da gravação/i }),
    );
    await user.click(
      screen.getByRole("button", { name: /confirmar e acessar/i }),
    );

    await waitFor(() => {
      expect(globalThis.alert).toHaveBeenCalledWith(
        "Participante não encontrado",
      );
    });

    caseLog.output = {
      alertCalls: globalThis.alert.mock.calls,
      navigateCalls: navigateMock.mock.calls,
    };
  });
});
