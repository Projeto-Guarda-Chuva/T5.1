// Home.tsx
import { useMemo, useState } from "react";
import { FaPlay, FaRegCalendarAlt } from "react-icons/fa";
import "./style.css";

const MOCK_VIDEOS = [
  {
    id: "1",
    date: "28 Abr 2026 às 14:30",
    thumbnail: "https://picsum.photos/seed/vid1/1280/720",
    src: "https://www.w3schools.com/html/mov_bbb.mp4",
  },
  {
    id: "2",
    date: "25 Abr 2026 às 09:15",
    thumbnail: "https://picsum.photos/seed/vid2/640/360",
    src: "https://www.w3schools.com/html/movie.mp4",
  },
  {
    id: "3",
    date: "20 Abr 2026 às 18:45",
    thumbnail: "https://picsum.photos/seed/vid3/640/360",
    src: "https://www.w3schools.com/html/mov_bbb.mp4",
  },
  {
    id: "4",
    date: "15 Abr 2026 às 10:00",
    thumbnail: "https://picsum.photos/seed/vid4/640/360",
    src: "https://www.w3schools.com/html/movie.mp4",
  },
];

export default function Home() {
  const [videos, setVideos] = useState(MOCK_VIDEOS);

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

  return (
    <div className="video-page">
      <div className="container-fluid px-3 px-lg-4">
        {/* Vídeo Atual */}
        <section className="featured-section">
          {latestVideo.id === MOCK_VIDEOS[0].id && (
            <h4 className="fw-bold mb-3 text-dark">Meu último vídeo</h4>
          )}
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
          <span>Outros vídeos</span>
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
    </div>
  );
}
