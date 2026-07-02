import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import VideoHistory from "../../../src/pages/VideoHistory";
import { formatDateTime } from "../../../src/utils/format";
import { registerCase } from "../../support/caseLog";

const useOperationLogMock = vi.fn();

vi.mock("../../../src/hooks/useOperationLog", () => ({
  default: () => useOperationLogMock(),
}));

describe("Gerente de Programa - Histórico da Operação", () => {
  beforeEach(() => {
    useOperationLogMock.mockReset();
  });

  it("lista registros de log com data, participante e status", () => {
    useOperationLogMock.mockReturnValue({
      operationLogs: {
        items: [
          {
            id: "sess-001",
            occurred_at: "2026-07-01T09:00:00Z",
            duration_seconds: 42,
            participant_email: "participante@example.com",
            status: "success",
            status_text: "Concluído",
            description: "Captura finalizada",
          },
        ],
        total: 1,
        message: "ok",
      },
      isLoading: false,
      error: null,
    });

    const caseLog = registerCase({
      input: {
        totalLogs: 1,
      },
      expected: {
        sessionId: "sess-001",
        participantEmail: "participante@example.com",
        statusText: "Concluído",
        occurredAt: formatDateTime("2026-07-01T09:00:00Z"),
      },
    });

    render(<VideoHistory />);

    expect(screen.getByText("sess-001")).toBeInTheDocument();
    expect(screen.getByText("participante@example.com")).toBeInTheDocument();
    expect(screen.getAllByText("Concluído")).toHaveLength(2);
    expect(
      screen.getByText(formatDateTime("2026-07-01T09:00:00Z")),
    ).toBeInTheDocument();

    caseLog.output = {
      renderedSessionId: screen.getByText("sess-001").textContent,
      renderedDate: screen.getByText(formatDateTime("2026-07-01T09:00:00Z"))
        .textContent,
      renderedStatus: screen.getAllByText("Concluído")[0].textContent,
    };
  });

  it("deveria informar claramente quando não existem registros de log", () => {
    useOperationLogMock.mockReturnValue({
      operationLogs: {
        items: [],
        total: 0,
        message: "Nenhum log encontrado.",
      },
      isLoading: false,
      error: null,
    });

    const caseLog = registerCase({
      input: {
        totalLogs: 0,
        message: "Nenhum log encontrado.",
      },
      expected: {
        emptyStateMessage: "Nenhum log encontrado.",
      },
      notes: [
        "Teste alinhado ao critério de aceitação de informar claramente a ausência de histórico.",
      ],
    });

    render(<VideoHistory />);

    caseLog.output = {
      renderedText: document.body.textContent,
    };

    expect(screen.getByText("Nenhum log encontrado.")).toBeInTheDocument();
  });
});
