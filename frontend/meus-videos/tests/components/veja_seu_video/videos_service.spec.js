import { beforeEach, describe, expect, it, vi } from "vitest";
import videosService from "../../../src/services/videosService";
import { registerCase } from "../../support/caseLog";

const apiGetMock = vi.fn();

vi.mock("../../../src/api", () => ({
  default: {
    get: (...args) => apiGetMock(...args),
  },
}));

describe("Aplicação Veja seu Vídeo - Serviço de Vídeos", () => {
  beforeEach(() => {
    apiGetMock.mockReset();
  });

  it("transforma o payload do backend e usa thumbnail padrão quando necessário", async () => {
    apiGetMock.mockResolvedValue({
      data: {
        items: [
          {
            id: "video-001",
            participant_video_id: "mongo-001",
            title: "Video",
            created_at: "2026-07-01T10:45:00Z",
            duration_seconds: 12,
            thumbnail_url: "",
            video_url: "https://cdn.example.com/video.mp4",
            status: "ready",
          },
        ],
      },
    });

    const caseLog = registerCase({
      input: {
        backendItems: 1,
      },
      expected: {
        id: "video-001",
        participantVideoId: "mongo-001",
        referenceDate: "2026-07-01",
        fallbackThumbnailPrefix: "data:image/svg+xml",
      },
    });

    const videos = await videosService.listVideos();

    expect(videos).toHaveLength(1);
    expect(videos[0]).toMatchObject({
      id: "video-001",
      participantVideoId: "mongo-001",
      referenceDate: "2026-07-01",
      src: "https://cdn.example.com/video.mp4",
    });
    expect(videos[0].thumbnail).toContain("data:image/svg+xml");

    caseLog.output = videos;
  });

  it("preserva a string original quando created_at é inválido", async () => {
    apiGetMock.mockResolvedValue({
      data: {
        items: [
          {
            id: "video-002",
            participant_video_id: undefined,
            title: "Video inválido",
            created_at: "data-invalida",
            duration_seconds: 5,
            thumbnail_url: "https://cdn.example.com/thumb.jpg",
            video_url: "",
            status: "ready",
          },
        ],
      },
    });

    const caseLog = registerCase({
      input: {
        created_at: "data-invalida",
      },
      expected: {
        date: "data-invalida",
      },
    });

    const videos = await videosService.listVideos();

    expect(videos[0].date).toBe("data-invalida");

    caseLog.output = videos[0];
  });
});
