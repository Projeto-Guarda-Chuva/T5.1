import { useEffect, useMemo, useState } from "react";
import { FaPlay, FaRegCalendarAlt, FaVideoSlash } from "react-icons/fa";
import "./style.css";
import Form from "../../components/Form";
import { sendParticipantVideoEmail } from "../../services/participantVideos";
import participantesService from "../../services/participantesService";
import videosService, { Video } from "../../services/videosService";

interface EmailFeedback {
  type: "success" | "danger";
  message: string;
}

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [participantId, setParticipantId] = useState<string | null>(null);
  const [initialLatestId, setInitialLatestId] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<EmailFeedback | null>(null);

  useEffect(() => {
    const loadPageData = async () => {
      try {
        setLoading(true);
        const [fetchedVideos, participant] = await Promise.all([
          videosService.listVideos(),
          participantesService.getCurrentParticipant().catch(() => null),
        ]);

        setVideos(fetchedVideos);
        setParticipantId(participant?.id ?? null);

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
    if (!participantId) {
      setEmailFeedback({
        type: "danger",
        message:
          "Não foi possível identificar o participante atual para enviar o vídeo.",
      });
      return;
    }

    if (!latestVideo?.referenceDate) {
      setEmailFeedback({
        type: "danger",
        message:
          "Este vídeo ainda não possui uma data de referência compatível com o backend.",
      });
      return;
    }

    try {
      setIsSendingEmail(true);
      setEmailFeedback(null);

      const response = await sendParticipantVideoEmail(
        participantId,
        latestVideo.referenceDate,
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
            <video
              key={latestVideo.id}
              controls
              poster={latestVideo.thumbnail}
              className="featured-video"
            >
              <source src={latestVideo.src} type="video/mp4" />
            </video>
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
                <img src={video.thumbnail} alt={video.date} />
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
