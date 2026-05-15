import api from "../api";

const DEFAULT_VIDEO_THUMBNAIL = `data:image/svg+xml;utf8,${encodeURIComponent(
  `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720">
    <defs>
      <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stop-color="#111827"/>
        <stop offset="100%" stop-color="#1f2937"/>
      </linearGradient>
    </defs>
    <rect width="1280" height="720" fill="url(#bg)"/>
    <circle cx="640" cy="360" r="92" fill="rgba(255,255,255,0.16)"/>
    <polygon points="610,305 610,415 710,360" fill="#ffffff"/>
    <text x="640" y="470" text-anchor="middle" fill="#e5e7eb" font-family="Arial, sans-serif" font-size="34">
      Vídeo salvo no MongoDB
    </text>
  </svg>`,
)}`;

export interface Video {
  id: string;
  participantVideoId?: string;
  date: string;
  thumbnail: string;
  src: string;
  referenceDate: string;
}

export interface BackendVideoResponse {
  id: string;
  participant_video_id?: string;
  title: string;
  created_at: string;
  duration_seconds: number;
  thumbnail_url: string;
  video_url: string;
  status: string;
}

export interface VideoListResponse {
  items: BackendVideoResponse[];
  total: number;
  message: string;
}

const formatVideoDisplayDate = (value: string): string => {
  const parsedDate = new Date(value);

  if (Number.isNaN(parsedDate.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(parsedDate).replace(",", " às");
};

const listVideos = async (): Promise<Video[]> => {
  const response = await api.get<VideoListResponse>("/videos");
  const items = response.data.items || [];

  // Transforma o formato do backend para o formato do frontend
  return items.map((video) => ({
    id: video.id,
    participantVideoId: video.participant_video_id,
    date: formatVideoDisplayDate(video.created_at),
    thumbnail: video.thumbnail_url || DEFAULT_VIDEO_THUMBNAIL,
    src: video.video_url || "",
    referenceDate: video.created_at.slice(0, 10),
  }));
};

export default {
  listVideos,
};
