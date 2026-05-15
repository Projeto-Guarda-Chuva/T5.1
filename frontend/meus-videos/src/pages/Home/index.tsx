import { useEffect, useMemo, useState } from "react";
import { FaPlay, FaRegCalendarAlt, FaVideoSlash } from "react-icons/fa";
import "./style.css";
import Form from "../../components/Form";
import {
  getParticipantVideoPlaybackUrl,
  sendParticipantVideoEmail,
} from "../../services/participantVideos";
import videosService, { Video } from "../../services/videosService";

interface EmailFeedback {
  type: "success" | "danger";
  message: string;
}

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [initialLatestId, setInitialLatestId] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<EmailFeedback | null>(null);
  const [featuredVideoSrc, setFeaturedVideoSrc] = useState<string>("");
  const [featuredVideoPoster, setFeaturedVideoPoster] = useState<string>("");
  const [isFeaturedVideoLoading, setIsFeaturedVideoLoading] = useState(false);
  const [featuredVideoLoadError, setFeaturedVideoLoadError] = useState<string | null>(null);
  const [videoThumbnailOverrides, setVideoThumbnailOverrides] = useState<
    Record<string, string>
  >({});

  useEffect(() => {
    const loadPageData = async () => {
      try {
        setLoading(true);
        const fetchedVideos = await videosService.listVideos();

        setVideos(fetchedVideos);

        if (fetchedVideos.length > 0) {
          setInitialLatestId(fetchedVideos[0].id);
        }
      } catch (error) {
        console.error("Erro ao carregar vídeos:", error);
        setVideos([]);
      } finally {
        setLoading(false);
      }
    };

    loadPageData();
  }, []);

  const latestVideo = useMemo(() => videos[0], [videos]);
  const otherVideos = useMemo(() => videos.slice(1), [videos]);

  useEffect(() => {
    let isCancelled = false;

    const loadVideoThumbnails = async () => {
      const thumbnailEntries = await Promise.all(
        videos.map(async (video) => {
          if (!video.participantVideoId) {
            return [video.id, video.thumbnail] as const;
          }

          try {
            const playbackUrl = await getParticipantVideoPlaybackUrl(
              video.participantVideoId,
            );
            const generatedPoster = await buildVideoPoster(playbackUrl);
            URL.revokeObjectURL(playbackUrl);

            if (generatedPoster) {
              return [video.id, generatedPoster] as const;
            }
          } catch {
            // Mantém o thumbnail atual como fallback.
          }

          return [video.id, video.thumbnail] as const;
        }),
      );

      if (!isCancelled) {
        setVideoThumbnailOverrides(Object.fromEntries(thumbnailEntries));
      }
    };

    if (videos.length === 0) {
      setVideoThumbnailOverrides({});
      return;
    }

    void loadVideoThumbnails();

    return () => {
      isCancelled = true;
    };
  }, [videos]);

  useEffect(() => {
    if (!latestVideo) {
      setFeaturedVideoSrc("");
      setFeaturedVideoPoster("");
      setIsFeaturedVideoLoading(false);
      setFeaturedVideoLoadError(null);
      return;
    }

    let isCancelled = false;
    let objectUrlToRevoke: string | null = null;

    setFeaturedVideoSrc("");
    setFeaturedVideoPoster(latestVideo.thumbnail);
    setIsFeaturedVideoLoading(true);
    setFeaturedVideoLoadError(null);

    const loadMongoBackedVideo = async () => {
      if (!latestVideo.participantVideoId) {
        if (!isCancelled) {
          setIsFeaturedVideoLoading(false);
          setFeaturedVideoLoadError(
            "Este vídeo ainda não está vinculado ao arquivo salvo no MongoDB.",
          );
        }
        return;
      }

      try {
        const playbackUrl = await getParticipantVideoPlaybackUrl(
          latestVideo.participantVideoId,
        );

        if (isCancelled) {
          URL.revokeObjectURL(playbackUrl);
          return;
        }

        objectUrlToRevoke = playbackUrl;
        setFeaturedVideoSrc(playbackUrl);
        const generatedPoster = await buildVideoPoster(playbackUrl);
        if (!isCancelled && generatedPoster) {
          setFeaturedVideoPoster(generatedPoster);
        }
        if (!isCancelled) {
          setIsFeaturedVideoLoading(false);
        }
      } catch {
        if (!isCancelled) {
          setFeaturedVideoSrc("");
          setFeaturedVideoPoster(latestVideo.thumbnail);
          setIsFeaturedVideoLoading(false);
          setFeaturedVideoLoadError(
            "Não foi possível carregar o arquivo deste vídeo salvo no MongoDB.",
          );
        }
      }
    };

    void loadMongoBackedVideo();

    return () => {
      isCancelled = true;
      if (objectUrlToRevoke) {
        URL.revokeObjectURL(objectUrlToRevoke);
      }
    };
  }, [latestVideo]);

  const handleVideoClick = (clickedVideoId: string) => {
    setVideos((prevVideos) => {
      const clickedVideo = prevVideos.find((video) => video.id === clickedVideoId);

      if (!clickedVideo) {
        return prevVideos;
      }

      const remainingVideos = prevVideos.filter((video) => video.id !== clickedVideoId);
      return [clickedVideo, ...remainingVideos];
    });
  };

  const handleSendVideoByEmail = async () => {
    if (!latestVideo?.referenceDate) {
      setEmailFeedback({
        type: "danger",
        message:
          "Este vídeo ainda não possui uma data de referência compatível com o backend.",
      });
      return;
    }

    if (!latestVideo?.participantVideoId) {
      setEmailFeedback({
        type: "danger",
        message:
          "Este vídeo exibido ainda não está vinculado ao arquivo correspondente no backend.",
      });
      return;
    }

    try {
      setIsSendingEmail(true);
      setEmailFeedback(null);

      const response = await sendParticipantVideoEmail(
        latestVideo.referenceDate,
        latestVideo.participantVideoId,
      );

      setEmailFeedback({
        type: "success",
        message: response.message,
      });
    } catch (error: any) {
      setEmailFeedback({
        type: "danger",
        message:
          error?.response?.data?.detail ||
          error?.message ||
          "Não foi possível enviar o vídeo por e-mail.",
      });
    } finally {
      setIsSendingEmail(false);
    }
  };

  if (loading) {
    return (
      <div className="video-page d-flex flex-column align-items-center justify-content-center">
        <div className="text-center p-4 p-md-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
          <p className="text-muted mt-3">Carregando seus vídeos...</p>
        </div>
      </div>
    );
  }

  if (videos.length === 0) {
    return (
      <>
        <div className="video-page d-flex flex-column align-items-center justify-content-center">
          <div className="text-center p-4 p-md-5">
            <div
              className="bg-primary rounded-circle shadow-sm d-inline-flex align-items-center justify-content-center mb-4"
              style={{ width: "100px", height: "100px" }}
            >
              <FaVideoSlash size={40} className="text-white" />
            </div>
            <h3 className="fw-bold text-dark mb-3">Nenhum vídeo por aqui</h3>
            <p
              className="text-muted mb-4 mx-auto"
              style={{ maxWidth: "400px" }}
            >
              Você ainda não possui nenhum vídeo salvo. <br></br> Que tal ir até
              o projeto e registrar a sua experiência?
            </p>
            <button
              type="button"
              className="btn btn-primary px-4"
              onClick={() => setIsFormOpen(true)}
            >
              Já participei
            </button>
          </div>
        </div>
        <Form
          isOpen={isFormOpen}
          onClose={() => setIsFormOpen(false)}
          onSubmit={(time) => {
            alert(
              `Participação confirmada às ${time}! Em breve o vídeo estará disponível.`,
            );
            setIsFormOpen(false);
          }}
        />
      </>
    );
  }

  return (
    <div className="video-page">
      <div className="container-fluid px-3 px-lg-4">
        <section className="featured-section">
          <div className="d-flex flex-column-reverse flex-md-row justify-content-between align-items-center align-items-md-center mb-3 gap-3">
            {latestVideo.id === initialLatestId ? (
              <h4 className="fw-bold text-dark mb-0">Meu último vídeo</h4>
            ) : (
              <div></div>
            )}

            <div className="d-flex flex-column flex-sm-row gap-2">
              <button
                type="button"
                className="btn btn-outline-primary px-4"
                onClick={handleSendVideoByEmail}
                disabled={isSendingEmail}
              >
                {isSendingEmail ? "Enviando..." : "Receber por e-mail"}
              </button>

              <button
                type="button"
                className="btn btn-primary px-4"
                onClick={() => setIsFormOpen(true)}
              >
                Nova participação
              </button>
            </div>
          </div>

          {emailFeedback ? (
            <div
              className={`alert alert-${emailFeedback.type} video-email-feedback`}
              role="alert"
            >
              {emailFeedback.message}
            </div>
          ) : null}

          <div className="featured-player">
            {isFeaturedVideoLoading ? (
              <div className="featured-video-state">
                <div className="spinner-border text-light" role="status">
                  <span className="visually-hidden">Carregando...</span>
                </div>
                <p className="featured-video-state-text">
                  Carregando o vídeo salvo no MongoDB...
                </p>
              </div>
            ) : featuredVideoLoadError ? (
              <div className="featured-video-state">
                <p className="featured-video-state-text">{featuredVideoLoadError}</p>
              </div>
            ) : (
              <video
                key={`${latestVideo.id}-${featuredVideoSrc}`}
                controls
                poster={featuredVideoPoster || latestVideo.thumbnail}
                className="featured-video"
                src={featuredVideoSrc}
              />
            )}
          </div>

          <div className="featured-date">
            <FaRegCalendarAlt />
            <span>{latestVideo.date}</span>
          </div>
        </section>

        <div className="video-divider">
          <span>Meus outros vídeos</span>
        </div>

        <section className="video-grid">
          {otherVideos.map((video) => (
            <div
              className="video-item"
              key={video.id}
              onClick={() => handleVideoClick(video.id)}
            >
              <div className="thumb-wrapper">
                <img
                  src={videoThumbnailOverrides[video.id] || video.thumbnail}
                  alt={video.date}
                />
                <div className="thumb-overlay">
                  <div className="play-btn">
                    <FaPlay />
                  </div>
                </div>
              </div>

              <div className="video-date">
                <FaRegCalendarAlt />
                <span>{video.date}</span>
              </div>
            </div>
          ))}
        </section>
      </div>

      <Form
        isOpen={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={(time) => {
          alert(
            `Participação confirmada às ${time}! Em breve o vídeo estará disponível.`,
          );
          setIsFormOpen(false);
        }}
      />
    </div>
  );
}

async function buildVideoPoster(videoSrc: string): Promise<string | null> {
  return await new Promise((resolve) => {
    const tempVideo = document.createElement("video");
    tempVideo.src = videoSrc;
    tempVideo.muted = true;
    tempVideo.playsInline = true;
    tempVideo.preload = "metadata";

    const cleanup = () => {
      tempVideo.removeAttribute("src");
      tempVideo.load();
    };

    tempVideo.addEventListener(
      "loadeddata",
      () => {
        const targetTime =
          Number.isFinite(tempVideo.duration) && tempVideo.duration > 0.2 ? 0.2 : 0;

        const captureFrame = () => {
          try {
            const canvas = document.createElement("canvas");
            canvas.width = tempVideo.videoWidth || 1280;
            canvas.height = tempVideo.videoHeight || 720;
            const context = canvas.getContext("2d");

            if (!context) {
              cleanup();
              resolve(null);
              return;
            }

            context.drawImage(tempVideo, 0, 0, canvas.width, canvas.height);
            const dataUrl = canvas.toDataURL("image/jpeg", 0.82);
            cleanup();
            resolve(dataUrl);
          } catch {
            cleanup();
            resolve(null);
          }
        };

        if (targetTime === 0) {
          captureFrame();
          return;
        }

        tempVideo.addEventListener("seeked", captureFrame, { once: true });
        tempVideo.currentTime = targetTime;
      },
      { once: true },
    );

    tempVideo.addEventListener(
      "error",
      () => {
        cleanup();
        resolve(null);
      },
      { once: true },
    );
  });
}
