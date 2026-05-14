// Home.tsx
import { useMemo, useState, useEffect } from "react";
import { FaPlay, FaRegCalendarAlt, FaVideoSlash } from "react-icons/fa";
import "./style.css";
import Form from "../../components/Form";
import { sendParticipantVideoEmail } from "../../services/participantVideos";

interface Video {
  id: string;
  date: string;
  thumbnail: string;
  src: string;
  referenceDate?: string;
}

interface LoggedUser {
  nome: string;
  email: string;
  participantId?: string;
}

interface EmailFeedback {
  type: "success" | "danger";
  message: string;
}

export default function Home() {
  const [videos, setVideos] = useState<Video[]>([]);
  const [loggedUser, setLoggedUser] = useState<LoggedUser | null>(null);
  const [initialLatestId, setInitialLatestId] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [isSendingEmail, setIsSendingEmail] = useState(false);
  const [emailFeedback, setEmailFeedback] = useState<EmailFeedback | null>(null);

  useEffect(() => {
    const loggedUserStr = localStorage.getItem("logged_user");
    if (loggedUserStr) {
      const user = JSON.parse(loggedUserStr);
      setLoggedUser(user);
      const userVideosStr = localStorage.getItem(`videos_${user.email}`);
      if (userVideosStr) {
        const parsedVideos = JSON.parse(userVideosStr);
        setVideos(parsedVideos);
        if (parsedVideos.length > 0) {
          setInitialLatestId(parsedVideos[0].id);
        }
      }
    }
  }, []);

  const latestVideo = useMemo(() => videos[0], [videos]);
  const otherVideos = useMemo(() => videos.slice(1), [videos]);

  const handleVideoClick = (clickedVideoId: string) => {
    setVideos((prevVideos) => {
      const clickedVideo = prevVideos.find((v) => v.id === clickedVideoId);
      if (!clickedVideo) return prevVideos;

      const remainingVideos = prevVideos
        .filter((v) => v.id !== clickedVideoId)
        .sort((a, b) => Number(a.id) - Number(b.id));

      return [clickedVideo, ...remainingVideos];
    });
  };

  const handleSendVideoByEmail = async () => {
    if (!loggedUser?.participantId) {
      setEmailFeedback({
        type: "danger",
        message:
          "Este usuário ainda não está vinculado a um participante do backend.",
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

    setIsSendingEmail(true);
    setEmailFeedback(null);

    try {
      const response = await sendParticipantVideoEmail(
        loggedUser.participantId,
        latestVideo.referenceDate,
      );
      setEmailFeedback({
        type: "success",
        message: response.message,
      });
    } catch (error) {
      setEmailFeedback({
        type: "danger",
        message:
          error instanceof Error
            ? error.message
            : "Não foi possível enviar o vídeo por e-mail.",
      });
    } finally {
      setIsSendingEmail(false);
    }
  };

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
        {/* Vídeo Atual */}
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

        {/* Separação */}
        <div className="video-divider">
          <span>Meus outros vídeos</span>
        </div>

        {/* Lista */}
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
