import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import Home from "../../../src/pages/Home";
import { ROUTES } from "../../../src/utils/routes";
import { registerCase } from "../../support/caseLog";

const navigateMock = vi.fn();
const useVideosMock = vi.fn();
const sendParticipantVideoEmailMock = vi.fn();
const getParticipantVideoPlaybackUrlMock = vi.fn();

vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock("../../../src/hooks/useVideos", () => ({
  useVideos: () => useVideosMock(),
}));

vi.mock("../../../src/services/participantVideos", () => ({
  sendParticipantVideoEmail: (...args) => sendParticipantVideoEmailMock(...args),
  getParticipantVideoPlaybackUrl: (...args) =>
    getParticipantVideoPlaybackUrlMock(...args),
}));

describe("Aplicação Veja seu Vídeo - Home", () => {
  beforeEach(() => {
    navigateMock.mockReset();
    useVideosMock.mockReset();
    sendParticipantVideoEmailMock.mockReset();
    getParticipantVideoPlaybackUrlMock.mockReset();
  });

  it("mostra estado de carregamento enquanto os vídeos ainda não chegaram", () => {
    useVideosMock.mockReturnValue({
      data: [],
      isLoading: true,
    });

    const caseLog = registerCase({
      input: {
        isLoading: true,
      },
      expected: {
        text: "Carregando seus vídeos...",
      },
    });

    render(<Home />);

    expect(screen.getByText("Carregando seus vídeos...")).toBeInTheDocument();

    caseLog.output = {
      renderedText: screen.getByText("Carregando seus vídeos...").textContent,
    };
  });

  it("mostra CTA quando não existem vídeos e navega para o fluxo de participação", async () => {
    useVideosMock.mockReturnValue({
      data: [],
      isLoading: false,
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        videos: [],
      },
      expected: {
        emptyState: "Nenhum vídeo por aqui",
        navigateTo: ROUTES.STATUS_GRAVACAO,
      },
    });

    render(<Home />);

    expect(screen.getByText("Nenhum vídeo por aqui")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /já participei/i }));

    expect(navigateMock).toHaveBeenCalledWith(ROUTES.STATUS_GRAVACAO);

    caseLog.output = {
      navigateCalls: navigateMock.mock.calls,
    };
  });

  it("bloqueia o envio por email quando o vídeo não possui data de referência", async () => {
    useVideosMock.mockReturnValue({
      data: [
        {
          id: "video-001",
          date: "01/07/2026 às 12:00",
          thumbnail: "thumb.jpg",
          src: "",
          referenceDate: "",
          participantVideoId: "mongo-001",
        },
      ],
      isLoading: false,
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        referenceDate: "",
        participantVideoId: "mongo-001",
      },
      expected: {
        feedback:
          "Este vídeo ainda não possui uma data de referência compatível com o backend.",
      },
    });

    render(<Home />);
    await user.click(screen.getByRole("button", { name: /receber por e-mail/i }));

    expect(
      screen.getByText(
        "Este vídeo ainda não possui uma data de referência compatível com o backend.",
      ),
    ).toBeInTheDocument();

    caseLog.output = {
      feedback: screen.getByRole("alert").textContent,
    };
  });

  it("bloqueia o envio por email quando o vídeo exibido não está vinculado ao backend", async () => {
    useVideosMock.mockReturnValue({
      data: [
        {
          id: "video-002",
          date: "01/07/2026 às 12:00",
          thumbnail: "thumb.jpg",
          src: "",
          referenceDate: "2026-07-01",
          participantVideoId: undefined,
        },
      ],
      isLoading: false,
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        referenceDate: "2026-07-01",
        participantVideoId: null,
      },
      expected: {
        feedback:
          "Este vídeo exibido ainda não está vinculado ao arquivo correspondente no backend.",
      },
    });

    render(<Home />);
    await user.click(screen.getByRole("button", { name: /receber por e-mail/i }));

    await waitFor(() => {
      expect(
        screen.getByText(
          "Este vídeo exibido ainda não está vinculado ao arquivo correspondente no backend.",
        ),
      ).toBeInTheDocument();
    });

    caseLog.output = {
      feedback: screen.getByRole("alert").textContent,
    };
  });

  it("destaca o vídeo mais recente e permite selecionar outro vídeo da lista", async () => {
    useVideosMock.mockReturnValue({
      data: [
        {
          id: "video-mais-recente",
          date: "02/07/2026 às 14:30",
          thumbnail: "thumb-recente.jpg",
          src: "",
          referenceDate: "2026-07-02",
          participantVideoId: undefined,
        },
        {
          id: "video-anterior",
          date: "01/07/2026 às 08:15",
          thumbnail: "thumb-anterior.jpg",
          src: "",
          referenceDate: "2026-07-01",
          participantVideoId: undefined,
        },
      ],
      isLoading: false,
    });

    const user = userEvent.setup();
    const caseLog = registerCase({
      input: {
        videos: ["video-mais-recente", "video-anterior"],
      },
      expected: {
        initialFeaturedDate: "02/07/2026 às 14:30",
        selectedFeaturedDate: "01/07/2026 às 08:15",
      },
    });

    const { container } = render(<Home />);

    const featuredDateBeforeClick = container.querySelector(".featured-date span");
    expect(featuredDateBeforeClick).toHaveTextContent("02/07/2026 às 14:30");
    expect(screen.getByText("Meu último vídeo")).toBeInTheDocument();

    await user.click(screen.getByText("01/07/2026 às 08:15"));

    const featuredDateAfterClick = container.querySelector(".featured-date span");
    expect(featuredDateAfterClick).toHaveTextContent("01/07/2026 às 08:15");
    expect(screen.queryByText("Meu último vídeo")).not.toBeInTheDocument();

    caseLog.output = {
      featuredDateBeforeClick: featuredDateBeforeClick?.textContent,
      featuredDateAfterClick: featuredDateAfterClick?.textContent,
    };
  });

  it("informa indisponibilidade quando o arquivo do vídeo não pode ser carregado", async () => {
    getParticipantVideoPlaybackUrlMock.mockRejectedValue(new Error("blob missing"));
    useVideosMock.mockReturnValue({
      data: [
        {
          id: "video-003",
          date: "03/07/2026 às 10:00",
          thumbnail: "thumb.jpg",
          src: "",
          referenceDate: "2026-07-03",
          participantVideoId: "mongo-003",
        },
      ],
      isLoading: false,
    });

    const caseLog = registerCase({
      input: {
        participantVideoId: "mongo-003",
        playbackUrlError: "blob missing",
      },
      expected: {
        feedback: "Não foi possível carregar o arquivo deste vídeo salvo no MongoDB.",
      },
    });

    render(<Home />);

    await waitFor(() => {
      expect(
        screen.getByText(
          "Não foi possível carregar o arquivo deste vídeo salvo no MongoDB.",
        ),
      ).toBeInTheDocument();
    });

    caseLog.output = {
      renderedMessage: screen.getByText(
        "Não foi possível carregar o arquivo deste vídeo salvo no MongoDB.",
      ).textContent,
    };
  });
});
